# Create 4x4 pane grid

split-window -h
split-window -v
select-pane -L
split-window -v
select-pane -U

# Pane 1 (top left)

select-pane -t 1

send "act" Enter
send "clear && py manage.py runserver" Enter

# Pane 2 (bottom left)

select-pane -t 2

send "act" Enter
send "cd networks" Enter
send "clear && rq worker" Enter

# Pane 3 (top right)

select-pane -t 3

send "clear && redis-server" Enter

# Pane 4 (bottom right)

select-pane -t 4

send "act && clear" Enter
