package k8s.allow

default allow = true

# Deny delete commands
deny contains msg if {
    regex.match("(?i).*kubectl\\s+delete.*", input.command)
    msg := "Delete commands are not allowed in this cluster."
}

# Deny commands missing a namespace specification
deny contains msg if {
    not ( regex.match("(?i).*--namespace=.*", input.command) 
          or regex.match("(?i).*\\-n\\s+\\S+.*", input.command) )
    msg := "No namespace provided in command. Defaulting to staging is required."
}