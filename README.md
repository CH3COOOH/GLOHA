# GLOHA
GLOHA (Global High Availability), run `gloha <config_filename.json> <-t|0~2>`.

# Solved Bugs

## bug-230306
Signal(2) cannot kill processes that launched by "nohup".

## bug-230228
Process out of control when a session is empty (all nodes died) and then the config is reloaded.

