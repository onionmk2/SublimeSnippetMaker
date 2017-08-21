import os
import glob

import sublime
import sublime_plugin

template = """<snippet>
<content><![CDATA[
%s
]]></content>
<tabTrigger>%s</tabTrigger>
<description>%s</description>
<scope>%s</scope>
</snippet>"""


class MakeSnippetCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.snippet_text = "\n".join(
            [self.view.substr(i) for i in self.view.sel()]
        )
        self.view.window().show_input_panel(
            'Trigger',
            '',
            self.set_trigger,
            None,
            None
        )

    def set_trigger(self, trigger):
        self.trigger = trigger
        self.view.window().show_input_panel(
            'Description',
            '',
            self.set_description,
            None,
            None
        )

    def set_description(self, description):
        self.description = description
        scopes = self.view.scope_name(
            self.view.sel()[0].begin()
        ).strip().replace(' ', ', ')
        self.view.window().show_input_panel(
            'Scope',
            scopes,
            self.set_scopes,
            None,
            None
        )

    def set_scopes(self, scopes):
        self.scopes = scopes
        self.ask_file_name()

    def ask_file_name(self):
        self.view.window().show_input_panel(
            'File Name',
            self.trigger + '.sublime-snippet',
            self.make_snippet,
            None,
            None
        )

    def make_snippet(self, file_name):
        settings = sublime.load_settings('Breadcrumbs.sublime-settings')
        location = settings.get('snippet_location', 'Snippets')

        file_path = os.path.join(
            sublime.packages_path(),
            'User',
            location,
            file_name
        )

        if os.path.exists(file_path) and not sublime.ok_cancel_dialog(
            'Override %s?' % file_name
        ):
            self.ask_file_name()
            return

        try:
            self.write_snippet(file_path)
        except OSError:
            sublime.error_message('Please specify a valid file name, i.e. `awesome.sublime-snippet`')  # noqa: E501
            self.ask_file_name()
        else:
            self.view.window().open_file(file_path)

    def write_snippet(self, file_path):
        file = open(file_path, "wb")
        snippet_xml = template % (
            self.snippet_text,
            self.trigger,
            self.description,
            self.scopes
        )
        file.write(bytes(snippet_xml, 'UTF-8'))
        file.close()


class EditSnippetCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings('Breadcrumbs.sublime-settings')
        location = settings.get('snippet_location', 'Snippets')
        snippets = [
            [os.path.basename(filepath), filepath] for filepath in glob.iglob(
                os.path.join(
                    sublime.packages_path(),
                    'User',
                    location,
                    '*.sublime-snippet'
                )
            )
        ]

        def on_done(index):
            if index >= 0:
                self.window.open_file(snippets[index][1])
            else:
                view = self.window.active_view()
                if self.window.get_view_index(view)[1] == -1:
                    view.close()

        def on_highlight(index):
            if index >= 0:
                self.window.open_file(snippets[index][1], sublime.TRANSIENT)

        self.window.show_quick_panel(
            [_[0] for _ in snippets],
            on_done,
            0,
            -1,
            on_highlight
        )
