class WhenConverter:
    regex = "past|future|all"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)
