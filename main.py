from setup import environment
from dashboard import Dashboard

environment.set_steps(500)
app = Dashboard(environment)
app.run()
