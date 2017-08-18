from os.path import join, isfile

from click import File


class EventAwareFile(File):
    def convert(self, value, param, ctx):
        file_name = value
        if not file_name.endswith(".json"):
            file_name += ".json"

        event_path = join(
            ctx.params.get("working_dir", ctx.obj.working_dir),
            ctx.params.get("function_name"),
            ".events",
            file_name
        )

        if isfile(event_path):
            return super(EventAwareFile, self).convert(event_path, param, ctx)

        return super(EventAwareFile, self).convert(value, param, ctx)
