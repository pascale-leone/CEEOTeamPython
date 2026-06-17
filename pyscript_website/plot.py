# plot.py — per-device Plotly chart management
# All Python dicts/lists passed to Plotly are converted to JS objects
# via json.dumps + js.JSON.parse — the only fully reliable conversion
# path in Pyodide since Plotly inspects object prototypes, not duck type.

import json
import math
from pyscript import document, window
from pyodide.ffi import create_proxy
import js   # Pyodide's js module — gives access to browser JS globals

_WINDOW = 200   # rolling point window per trace

# ── Colour palettes ──────────────────────────────────────────────────
_COLORS = {
    'left':       '#3B82F6',
    'right':      '#A78BFA',
    'single':     '#3B82F6',
    'hue':        '#F59E0B',
    'saturation': '#EC4899',
    'reflection': '#14B8A6',
    'red':        '#EF4444',
    'green':      '#22C55E',
    'blue_ch':    '#3B82F6',
    'ctrl_left':  '#06B6D4',
    'ctrl_right': '#F97316',
}

COLOR_MAP = {
    'No color': '#E5E7EB', 'Red':     '#EF4444', 'Yellow':  '#EAB308',
    'Blue':     '#3B82F6', 'Teal':    '#14B8A6', 'Green':   '#22C55E',
    'Purple':   '#A855F7', 'White':   '#F9FAFB', 'Magenta': '#EC4899',
    'Orange':   '#F97316', 'Azure':   '#38BDF8',
}

COLOR_INT_MAP = {
    0:'No color', 1:'Red',  2:'Yellow', 3:'Blue', 4:'Teal',
    5:'Green',    6:'Purple',7:'White', 8:'Magenta',9:'Orange', 10:'Azure',
}


def _to_js(obj):
    """Convert any Python dict/list to a JS object via JSON round-trip.
    This is the only fully reliable conversion for Plotly in Pyodide —
    Plotly checks object prototypes internally, so plain JsProxy dicts fail."""
    return js.JSON.parse(json.dumps(obj))


def _safe(val):
    try:
        if math.isnan(val):
            return None
    except TypeError:
        pass
    return val


# ── Tab registry ─────────────────────────────────────────────────────
_plot_registry = {}   # uid → DevicePlot

# Initialise the JS callback dispatch table as a plain JS object
# so JS can access it with bracket notation: window._metricCallbacks[uid]
window._metricCallbacks = js.Object.new()


def _activate_plot_tab(uid):
    for tab in document.querySelectorAll('#plot-tab-strip .plot-tab'):
        tab.classList.remove('active')
    for panel in document.querySelectorAll('#plot-container .chart-panel'):
        panel.classList.remove('active')
    tab = document.getElementById(f'plot-tab-{uid}')
    div = document.getElementById(f'plot-div-{uid}')
    if tab: tab.classList.add('active')
    if div: div.classList.add('active')


class DevicePlot:
    """One Plotly chart per connected device."""

    def __init__(self, uid, device_type, device_label):
        self.uid             = uid
        self.device_type     = device_type
        self.device_label    = device_label
        self._plot_div_id    = f'plot-div-{uid}'
        self._tab_id         = f'plot-tab-{uid}'
        self._active_metric  = 'speed'
        self._metric_list    = []
        self._metric_ranges  = {}

        self._inject_tab_and_div()
        self._init_plotly()
        self._register_callbacks()

        # Hide the "connect a device" placeholder once we have a real tab
        empty = document.getElementById('plot-empty-msg')
        if empty:
            empty.style.display = 'none'

    # ── DOM injection ────────────────────────────────────────────
    def _inject_tab_and_div(self):
        tab_strip = document.getElementById('plot-tab-strip')

        tab = document.createElement('button')
        tab.id        = self._tab_id
        tab.className = 'plot-tab'
        tab.innerHTML = (
            f'<span class="tab-dot" style="background:{self._tab_color()}"></span>'
            f' {self._short_label()}'
        )
        tab.setAttribute('onclick', f"window._activatePlotTab('{self.uid}')")
        tab_strip.appendChild(tab)

        container = document.getElementById('plot-container')

        if self.device_type == 'cs':
            wrapper = document.createElement('div')
            wrapper.id        = self._plot_div_id
            wrapper.className = 'chart-panel'
            wrapper.style.height = '100%'
            wrapper.innerHTML = (
                f'<div class="color-display">'
                f'  <div class="color-tile" id="color-tile-{self.uid}"></div>'
                f'  <div class="color-name" id="color-label-{self.uid}">No color</div>'
                f'</div>'
                f'<div class="metric-row" id="metric-row-{self.uid}">'
                f'  <button class="metric-btn active" data-trace="0" '
                f'    onclick="window._toggleCsTrace(\'{self.uid}\',0,this)">Hue</button>'
                f'  <button class="metric-btn" data-trace="1" '
                f'    onclick="window._toggleCsTrace(\'{self.uid}\',1,this)">Saturation</button>'
                f'  <button class="metric-btn" data-trace="2" '
                f'    onclick="window._toggleCsTrace(\'{self.uid}\',2,this)">Reflection</button>'
                f'  <button class="metric-btn" data-trace="3" '
                f'    onclick="window._toggleCsTrace(\'{self.uid}\',3,this)">Red</button>'
                f'  <button class="metric-btn" data-trace="4" '
                f'    onclick="window._toggleCsTrace(\'{self.uid}\',4,this)">Green</button>'
                f'  <button class="metric-btn" data-trace="5" '
                f'    onclick="window._toggleCsTrace(\'{self.uid}\',5,this)">Blue</button>'
                f'</div>'
                f'<div id="cs-chart-{self.uid}" class="plotly-div" style="flex:1;min-height:0;"></div>'
            )
            container.appendChild(wrapper)
            self._plotly_target = f'cs-chart-{self.uid}'

        elif self.device_type in ('sm', 'dm'):
            wrapper = document.createElement('div')
            wrapper.id        = self._plot_div_id
            wrapper.className = 'chart-panel'
            wrapper.style.height = '100%'
            motor_metrics = [
                ('speed',            'Speed'),
                ('power',            'Power'),
                ('position',         'Position'),
                ('absolutePosition', 'Abs. Pos.'),
            ]
            btn_html = ''.join(
                f'<button class="metric-btn{"  active" if m == "speed" else ""}"'
                f' data-metric="{m}"'
                f' onclick="window._setMotorMetric(\'{self.uid}\',\'{m}\',this)">'
                f'{label}</button>'
                for m, label in motor_metrics
            )
            wrapper.innerHTML = (
                f'<div class="metric-row" id="metric-row-{self.uid}">{btn_html}</div>'
                f'<div id="motor-chart-{self.uid}" class="plotly-div"'
                f' style="flex:1;min-height:0;"></div>'
            )
            container.appendChild(wrapper)
            self._plotly_target = f'motor-chart-{self.uid}'

        else:
            # Controller — no metric switcher needed
            div = document.createElement('div')
            div.id        = self._plot_div_id
            div.className = 'chart-panel'
            div.style.height = '100%'
            container.appendChild(div)
            self._plotly_target = self._plot_div_id

        if tab_strip.querySelectorAll('.plot-tab').length == 1:
            _activate_plot_tab(self.uid)

    # ── Register Python callbacks into JS dispatch table ────────
    def _register_callbacks(self):
        self._proxy_set_metric   = create_proxy(self.set_motor_metric)
        self._proxy_toggle_trace = create_proxy(self.toggle_cs_trace)

        cb = js.Object.new()
        cb.setMetric   = self._proxy_set_metric
        cb.toggleTrace = self._proxy_toggle_trace
        # Use js.Reflect.set to assign onto the JsProxy without Python
        # item-assignment syntax, which JsProxy does not support.
        js.Reflect.set(window._metricCallbacks, self.uid, cb)

    def _tab_color(self):
        return {'sm':'#3B82F6','dm':'#A78BFA','cs':'#22C55E','c':'#06B6D4'}.get(
            self.device_type, '#6B7280')

    def _short_label(self):
        return {'sm':'sm','dm':'dm','cs':'cs','c':'c'}.get(
            self.device_type, self.device_type)

    # ── Layout helper ────────────────────────────────────────────
    def _make_layout(self, y_range=None, y_title='Value'):
        layout = {
            'margin':         {'l': 42, 'r': 10, 't': 10, 'b': 30},
            'paper_bgcolor':  'rgba(0,0,0,0)',
            'plot_bgcolor':   '#FAFAFA',
            'xaxis': {
                'showticklabels': False,
                'showgrid':       False,
                'zeroline':       False,
            },
            'yaxis': {
                'title':     {'text': y_title, 'font': {'size': 10}},
                'tickfont':  {'size': 9},
                'autorange': y_range is None,
            },
            'legend':     {'font': {'size': 10}, 'orientation': 'h', 'y': -0.15},
            'showlegend': True,
        }
        if y_range is not None:
            layout['yaxis']['range']     = list(y_range)
            layout['yaxis']['autorange'] = False
        return layout

    def _empty_trace(self, name, color, dash='solid', visible=True):
        return {
            'x':       [],
            'y':       [],
            'mode':    'lines',
            'name':    name,
            'visible': visible,
            'line':    {'color': color, 'width': 2, 'dash': dash},
            'type':    'scatter',
        }

    # ── Plotly init ──────────────────────────────────────────────
    def _init_plotly(self):
        dispatch = {
            'sm': self._init_motor_plot,
            'dm': self._init_motor_plot,
            'cs': self._init_color_sensor_plot,
            'c':  self._init_controller_plot,
        }
        dispatch.get(self.device_type, lambda: None)()

    def _init_motor_plot(self):
        is_double = self.device_type == 'dm'
        metrics = [
            ('speed',            'Speed',            (-100, 100)),
            ('power',            'Power',            (-100, 100)),
            ('position',         'Position (°)',     None),
            ('absolutePosition', 'Abs. Pos. (°)',    (0, 360)),
        ]
        self._metric_list   = [m[0] for m in metrics]
        self._metric_ranges = {m[0]: m[2] for m in metrics}

        traces = []
        for metric, label, _ in metrics:
            visible = (metric == 'speed')
            if is_double:
                traces.append(self._empty_trace(f'{label} L', _COLORS['left'],  visible=visible))
                traces.append(self._empty_trace(f'{label} R', _COLORS['right'], 'dash', visible=visible))
            else:
                traces.append(self._empty_trace(label, _COLORS['single'], visible=visible))

        layout = self._make_layout(y_range=(-100, 100), y_title='Speed')
        config = {'responsive': True, 'displayModeBar': False}

        window.Plotly.newPlot(
            self._plotly_target,
            _to_js(traces),
            _to_js(layout),
            _to_js(config),
        )

    def _init_color_sensor_plot(self):
        traces = [
            self._empty_trace('Hue',        _COLORS['hue'],        visible=True),
            self._empty_trace('Saturation', _COLORS['saturation'], visible=False),
            self._empty_trace('Reflection', _COLORS['reflection'], visible=False),
            self._empty_trace('Red',        _COLORS['red'],        visible=False),
            self._empty_trace('Green',      _COLORS['green'],      visible=False),
            self._empty_trace('Blue',       _COLORS['blue_ch'],    visible=False),
        ]
        layout = self._make_layout(y_title='Value')
        config = {'responsive': True, 'displayModeBar': False}

        window.Plotly.newPlot(
            self._plotly_target,
            _to_js(traces),
            _to_js(layout),
            _to_js(config),
        )

    def _init_controller_plot(self):
        traces = [
            self._empty_trace('Left stick',  _COLORS['ctrl_left'],  visible=True),
            self._empty_trace('Right stick', _COLORS['ctrl_right'], visible=True),
        ]
        layout = self._make_layout(y_range=(-100, 100), y_title='Position %')
        config = {'responsive': True, 'displayModeBar': False}

        window.Plotly.newPlot(
            self._plotly_target,
            _to_js(traces),
            _to_js(layout),
            _to_js(config),
        )

    # ── Data push ────────────────────────────────────────────────
    def push_motor(self, sensor, side_idx=None):
        """Push one notification's motor data. side_idx: None=SM, 0=left DM, 1=right DM."""
        is_double = self.device_type == 'dm'
        vals = [
            _safe(sensor.speed),
            _safe(sensor.power),
            _safe(sensor.position),
            _safe(sensor.absolutePosition),
        ]
        t = window.performance.now() / 1000.0

        indices, xs, ys = [], [], []
        for m_idx, val in enumerate(vals):
            if val is None:
                continue
            trace_idx = (m_idx * 2 + side_idx) if is_double else m_idx
            indices.append(trace_idx)
            xs.append([t])
            ys.append([val])

        if not indices:
            return

        window.Plotly.extendTraces(
            self._plotly_target,
            _to_js({'x': xs, 'y': ys}),
            _to_js(indices),
            _WINDOW,
        )

    def push_color_sensor(self, sensor):
        vals = [
            _safe(sensor.hue),
            _safe(sensor.saturation),
            _safe(sensor.reflection),
            _safe(sensor.rawRed),
            _safe(sensor.rawGreen),
            _safe(sensor.rawBlue),
        ]
        t = window.performance.now() / 1000.0
        indices = [i for i, v in enumerate(vals) if v is not None]
        if not indices:
            return

        window.Plotly.extendTraces(
            self._plotly_target,
            _to_js({'x': [[t] for _ in indices], 'y': [[vals[i]] for i in indices]}),
            _to_js(indices),
            _WINDOW,
        )

        # Update color tile
        c_int  = sensor.color
        c_name = 'No color'
        if not (isinstance(c_int, float) and math.isnan(c_int)):
            c_name = COLOR_INT_MAP.get(int(c_int), 'No color')
        tile  = document.getElementById(f'color-tile-{self.uid}')
        label = document.getElementById(f'color-label-{self.uid}')
        if tile and label:
            tile.style.backgroundColor = COLOR_MAP.get(c_name, '#E5E7EB')
            label.innerText = c_name
            label.style.color = (
                '#111827' if c_name in ('White', 'Yellow', 'Azure', 'No color')
                else '#fff'
            )

    def push_controller(self, sensor):
        left  = _safe(sensor.leftPercent)
        right = _safe(sensor.rightPercent)
        if left is None and right is None:
            return
        t = window.performance.now() / 1000.0
        indices, xs, ys = [], [], []
        if left  is not None: indices.append(0); xs.append([t]); ys.append([left])
        if right is not None: indices.append(1); xs.append([t]); ys.append([right])

        window.Plotly.extendTraces(
            self._plotly_target,
            _to_js({'x': xs, 'y': ys}),
            _to_js(indices),
            _WINDOW,
        )

    # ── Color sensor individual trace toggle ────────────────────
    def toggle_cs_trace(self, trace_idx, visible):
        window.Plotly.restyle(
            self._plotly_target,
            _to_js({'visible': visible}),
            _to_js([trace_idx]),
        )

    # ── Motor metric switching ───────────────────────────────────
    def set_motor_metric(self, metric):
        if self.device_type not in ('sm', 'dm'):
            return
        is_double = self.device_type == 'dm'
        visibility = []
        for m in self._metric_list:
            show = (m == metric)
            visibility += [show, show] if is_double else [show]

        window.Plotly.restyle(
            self._plotly_target,
            _to_js({'visible': visibility}),
        )
        y_range = self._metric_ranges.get(metric)
        if y_range is not None:
            window.Plotly.relayout(
                self._plotly_target,
                _to_js({'yaxis.range': list(y_range), 'yaxis.autorange': False}),
            )
        else:
            window.Plotly.relayout(
                self._plotly_target,
                _to_js({'yaxis.autorange': True}),
            )
        self._active_metric = metric

    # ── Cleanup ──────────────────────────────────────────────────
    def destroy(self):
        # Unregister callbacks
        if hasattr(window, '_metricCallbacks'):
            try:
                del window._metricCallbacks[self.uid]
            except Exception:
                pass
        # Free proxies
        for attr in ('_proxy_set_metric', '_proxy_toggle_trace'):
            p = getattr(self, attr, None)
            if p:
                try: p.destroy()
                except Exception: pass
        tab = document.getElementById(self._tab_id)
        div = document.getElementById(self._plot_div_id)
        if tab: tab.remove()
        if div:
            try:
                window.Plotly.purge(self._plotly_target)
            except Exception:
                pass
            div.remove()

        # If no tabs left, show the empty message again
        remaining = document.querySelectorAll('#plot-tab-strip .plot-tab')
        if remaining.length == 0:
            empty = document.getElementById('plot-empty-msg')
            if empty:
                empty.style.display = ''
        else:
            first_uid = remaining[0].id.replace('plot-tab-', '')
            _activate_plot_tab(first_uid)