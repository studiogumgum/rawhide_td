import os
param = '-n' if os.sys.platform.lower()=='win32' else '-c'
hostname = "8.8.8.8" #example
response = os.system(f"ping {param} 1 {hostname}")

if response == 0:
  if parent.Status.par.Internetconnection == 0:
    parent.Status.par.Internetconnection = 1
    op.LOGGER.Info('Internet Connected')
else:
  if parent.Status.par.Internetconnection == 1:
    parent.Status.par.Internetconnection = 0
    op.LOGGER.Info('Internet Disconnected')