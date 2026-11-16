"""Deterministic plain-English copy and standards-compliant draft email."""
from email.message import EmailMessage
from email.policy import SMTP
from .adapters import text


def draft(result, demo=False):
    prefix = '[DEMO] ' if demo else ''
    subject = f"{prefix}Corridor Lifeline | {result['level']} | {text(result['corridor'])}"
    status = result['rail_status']
    action = ('Contact your rail operator before dispatch and review stock and delivery commitments. '
              'Do not assume an alternative road route is open.' if status == 'closed' else
              'Check service availability with your rail operator and review time-sensitive shipments.'
              if result['score'] >= 25 else
              'Continue routine checks with your rail operator; this score does not confirm the route is safe or open.')
    if result['issues'] and status != 'closed':
        action = 'Verify the missing or outdated information with the source and your rail operator before dispatch. ' + action
    lines = [f"Corridor: {text(result['corridor'])}", f"As of: {result['as_of']} (UTC)",
             f"Risk indicator: {result['level']} - {result['score']}/100.",
             f"Data coverage: {result['coverage']}.", f"Latest usable rail input: {status}.", '',
             'What this means:', action, '', 'Why this score:']
    lines.extend('- ' + text(reason) for reason in result['reasons'])
    if result['issues']:
        lines += ['', 'Information gaps - verify before acting:']
        lines.extend('- ' + text(issue) for issue in result['issues'])
    lines += ['', 'The score adds rainfall, warning and rail points, capped at 100. '
              'It is a rule-based indicator, not a closure probability or an advance-warning guarantee.',
              'Rainfall is since local 9 am, not a rolling 24-hour total. '
              'Warning matches need manual geographic confirmation.', '', 'Sources:']
    lines.extend('- ' + text(url) for url in result['sources'])
    if demo:
        lines += ['', 'DEMO ONLY: event facts are sourced; weather and warning adapter inputs are illustrative. '
                  'Replay timestamps are scenario clocks. This is not a validated historical backtest.']
    body = '\n'.join(lines) + '\n'
    message = EmailMessage(policy=SMTP)
    message['Subject'] = subject
    message.set_content(body)
    return subject + '\n\n' + body, message.as_bytes()
