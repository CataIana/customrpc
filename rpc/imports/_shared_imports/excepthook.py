from collections import namedtuple
from traceback import format_exception
from discord_webhook import DiscordWebhook

def customExceptHook(self, type_, value, traceback):
    traceback_extended = _add_missing_frames(traceback) if traceback else traceback
    formatted = ''.join(format_exception(type_, value, traceback_extended))
    self.log.error(f"Uncaught exception: {formatted}")

    if self.stderr_webhook:
        webhook = DiscordWebhook(
            url="https://discordapp.com/api/webhooks/714899533213204571/Wa6iiaUBG9Y5jX7arc6-X7BYcY-0-dAjQDdSIQkZPpy_IPGT2NrNhAC_ibXSOEzHyKzz",
            content=f"```python\n{formatted}```"
        )
        webhook.execute()

def _add_missing_frames(tb):
    result = fake_tb(tb.tb_frame, tb.tb_lasti, tb.tb_lineno, tb.tb_next)
    frame = tb.tb_frame.f_back
    while frame:
        result = fake_tb(frame, frame.f_lasti, frame.f_lineno, result)
        frame = frame.f_back
    return result

fake_tb = namedtuple(
    'fake_tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next')
)
