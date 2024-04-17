#!/bin/sh

echo "Hello Concourse"

if [ ! "personas.json" ]; then
    echo "Error: File 'personas.json' not found."
    exit 1
fi

greeted_file="greeted.txt"
if [ ! $greeted_file ]; then
    touch "$greeted_file"
fi

# Get all names
names=$(jq -r '.[].name' personas.json)

for name in $names; do
    if ! grep -q "^$name$" "$greeted_file"; then
        # Greet the person
        echo "Hello to SAP, $name"
        # Add the greeted person to the list
        echo "$name" >> "$greeted_file"
    else
        # Output that the person is already welcomed
        echo "Person $name is already welcomed"
    fi
done

# Commit and push changes to the repository
git add "$greeted_file"
git commit -m "Update greeted.txt"