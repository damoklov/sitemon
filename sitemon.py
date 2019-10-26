import gi
import threading
import time
import subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


STOP_THREADING = False


class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='DOMAINMON')
        self.domains = Gtk.ListStore(str, str)
        self.connect('delete-event', Gtk.main_quit)
        self.tree = Gtk.TreeView(model=self.domains)
        self.set_default_size(900, 300)
        self.set_resizable(False)

        renderer = Gtk.CellRendererText()
        renderer.set_property("editable", True)
        renderer.connect("edited", self.text_edited)

        # Add column #1 with domain names
        domain_name = Gtk.TreeViewColumn('Domain', renderer, text=0)
        domain_name.set_sort_column_id(0)
        self.tree.append_column(domain_name)

        # Add column #2 with status
        domain_status = Gtk.TreeViewColumn('Status', renderer, text=1)
        domain_status.set_sort_column_id(1)
        self.tree.append_column(domain_status)

        # Add scrollbar for window
        window_scroll = Gtk.ScrolledWindow()
        window_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        window_scroll.add(self.tree)
        window_scroll.set_min_content_height(250)

        # Add buttons
        button_plus = Gtk.Button(label='+')
        button_minus = Gtk.Button(label='-')
        button_refresh = Gtk.Button(label='Refresh')
        button_switch = Gtk.Switch()
        button_switch.set_active(False)

        button_plus.connect('clicked', self.on_plus_button_clicked)
        button_minus.connect('clicked', self.on_minus_button_clicked)
        button_switch.connect("notify::active", self.on_switch_activated)
        button_refresh.connect("clicked", self.update_progress)

        # Pack whole view
        box = Gtk.Box()
        box.pack_start(window_scroll, True, True, 1)
        box.pack_start(button_minus, False, False, 1)
        box.pack_start(button_plus, False, False, 2)
        box.pack_start(button_switch, True, True, 2)
        box.pack_start(button_refresh, False, False, 0)

        self.add(box)
        self.show_all()

    def text_edited(self, widget, path, text):
        self.domains[path][1] = text

    def on_switch_activated(self, switch, widget):
        global STOP_THREADING
        if switch.get_active():
            STOP_THREADING = False
            thread = threading.Thread(target=self.example_target)
            thread.daemon = True
            thread.start()
        else:
            STOP_THREADING = True

    def on_minus_button_clicked(self, button):
        domain_selection = self.tree.get_selection()
        domain, paths = domain_selection.get_selected_rows()

        for path in paths:
            path_iter = domain.get_iter(path)
            domain.remove(path_iter)

    def on_plus_button_clicked(self, widget):
        domain = self.get_user_domain(self, "Enter Domain Name", "Domain")
        if domain:
            self.domains.append([domain, "N/A"])

    @staticmethod
    def get_user_domain(parent, message, title):
        mod = Gtk.DialogFlags.MODAL
        dest = Gtk.DialogFlags.DESTROY_WITH_PARENT
        qst = Gtk.MessageType.QUESTION
        resp = Gtk.ButtonsType.OK_CANCEL

        dialog_window = Gtk.MessageDialog(parent, mod | dest, qst, resp, text=message)
        dialog_window.set_title(title)

        dialog_box = dialog_window.get_content_area()
        user_domain = Gtk.Entry()
        user_domain.set_size_request(250, 0)
        dialog_box.pack_end(user_domain, False, False, 0)

        dialog_window.show_all()
        response = dialog_window.run()
        text = user_domain.get_text()
        dialog_window.destroy()

        if response == Gtk.ResponseType.OK and text != str():
            return text
        else:
            return None

    def update_progress(self, widget=None):
        for i in range(len(self.domains)):
            hostname = self.domains[i][0]
            try:
                subprocess.check_call(['ping', '-c', '1', '-W', '1', hostname])
                is_up = True
            except subprocess.CalledProcessError:
                is_up = False
            if is_up:
                status = "UP"
            else:
                status = "DOWN"
            self.domains[i][1] = str(status)

    def example_target(self):
        global STOP_THREADING
        while True:
            GLib.idle_add(self.update_progress)
            time.sleep(5)
            if STOP_THREADING:
                break


win = MyWindow()
win.default_height = 1000
Gtk.main()

