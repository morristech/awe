import os
import time
import webbrowser

from . import messages
from . import registry
from . import view
from . import webserver
from . import websocket
from . import export

page = None

DEFAULT_WIDTH = 1200


class Page(view.Element):

    def __init__(
            self,
            title='Awe',
            port=8080,
            width=None,
            style=None,
            export_fn=None,
            offline=False):
        """
        :param title: Page title.
        :param port: Webserver port.
        :param width: Set the page content width. (defaults to ``1200px``)
        :param style: Set custom javascript style object.
        :param export_fn: Override default export function.
        :param offline: Offline mode means start/block don't do anything. Useful when exporting directly from python.
        """
        super(Page, self).__init__(parent=None, element_id='', props=None, style=None)
        self._offline = (offline or os.environ.get('AWE_OFFLINE'))
        self._port = port
        self._title = title
        self._style = self._set_default_style(style, width)
        self._registry = registry.Registry()
        self._message_handler = messages.MessageHandler(self._registry, self._dispatch)
        self._exporter = export.Exporter(
            export_fn=export_fn,
            get_initial_state=self._get_initial_state)
        self._server = webserver.WebServer(
            exporter=self._exporter,
            port=port)
        self._ws_server = websocket.WebSocketServer(self._message_handler)
        self._started = False
        self._version = 0
        self._closed = False
        if os.environ.get('AWE_SET_GLOBAL'):
            global page
            page = self

    def start(self, block=False, open_browser=True, develop=False):
        """
        Start the page services.

        :param block: Should the method invocation block. (default: ``False``)
        :param open_browser: Should a new tab be opened in a browser pointing to the started page. (default: ``True``)
        :param develop: During development, changes to port for open browser to ``3000``.
               (due to npm start, default ``False``)
        """
        if self._offline:
            return
        self._message_handler.start()
        self._server.start()
        self._ws_server.start()
        self._started = True
        if open_browser:
            port = 3000 if (develop or os.environ.get('AWE_DEVELOP')) else self._port
            webbrowser.open_new_tab('http://localhost:{}'.format(port))
        if block:
            self.block()

    def export(self, export_fn=None):
        """
        Export current page state into a static html.

        :param export_fn: Override the export_fn supplied during page creation. (if any)
        :return: The exporter result.
        """
        return self._exporter.export(export_fn)

    def block(self):
        """
        Utility method to block after page has been started.
        """
        if self._offline:
            return
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def close(self):
        self._closed = True

    def _get_initial_state(self):
        return {
            'children': [t._get_view() for t in self.children],
            'variables': self._registry.get_variables(),
            'version': self._version,
            'style': self._style,
            'title': self._title,
        }

    def _increase_version(self):
        self._version += 1

    def _register(self, obj, obj_id=None):
        self._registry.register(obj, obj_id)

    def _unregister(self, obj, obj_id=None):
        self._registry.unregister(obj, obj_id)

    def _dispatch(self, action, client_id=None):
        if self._closed:
            raise RuntimeError('page is closed')
        self._increase_version()
        if not self._started:
            return
        action['version'] = self._version
        self._ws_server.dispatch_from_thread(action, client_id)

    @staticmethod
    def _set_default_style(style, width):
        style = style or {}
        defaults = {
            'width': width or DEFAULT_WIDTH,
            'paddingTop': '6px',
            'paddingBottom': '6px'
        }
        for key, default in defaults.items():
            style.setdefault(key, default)
        return style
