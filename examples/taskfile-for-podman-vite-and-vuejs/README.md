This uses [Task (taskfile.dev)](https://taskfile.dev/) to run the commands.
It uses [Podman](https://podman.io/), which unlike Docker helpfully doesn't require root and makes it easier to avoid permissions issues during development.
It uses create-vue to set up a [Vue.js](https://vuejs.org/) 3 project with Vite.


# Prerequisites
You must already have installed Task and Podman.

# Usage

## First run

1. Before you start, customise Taskfile.yml for your project
2. If it's a new project, initialise it: `task vue:init`
3. Start the dev server: `task vue:dev`

## NPM

Here's an example showing how to run an NPM command in the container:

```bash
task vue:npm -- install luxon --save
```

## Other

Other commands: `task --summary`

