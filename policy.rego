package k8s.allow

import rego.v1

default allow = true

# Deny delete commands
deny contains msg if {
    regex.match("(?i).*kubectl\\s+delete.*", input.command)
    msg := "Delete commands are not allowed in this cluster."
}

# Deny commands missing a namespace specification,
# but exempt "kubectl create namespace" commands.
deny contains msg if {
    not regex.match("(?i).*kubectl\\s+create\\s+namespace.*", input.command)
    not regex.match("(?i).*--namespace=.*", input.command)
    not regex.match("(?i).*\\-n\\s+\\S+.*", input.command)
    msg := "No namespace provided in command. Defaulting to staging is required."
}

# Deny commands containing placeholder values (e.g., text inside angle brackets)
deny contains msg if {
    regex.match("(?i).*<[^>]+>.*", input.command)
    msg := "Command contains placeholder values. Please replace with actual resource names."
}
