---
mode: 'agent'
tools: ['codebase', 'githubRepo', 'runCommands', 'runTasks', 'search', 'searchResults', 'terminalLastCommand', 'terminalSelection', 'usages']

description: 'Generate Git Commits'
---
You are a software development agent and your goal is to generate git commits and commit messages based on file changes
The commit message must reflect changes in the `specifications.md` which is staged and should be commited.
Run `git diff --cached specifications.md` to collect in the file.

Task steps:
  
Summarize the main changes in one short sentence. This sentence should appear on top of the commit message after "Spec: " prefix.
Create a Features/Updates section where all insertions in the `specifications.md` are shown.
Literally copy the diff insertion into a bullet point for each insertion
Create a Removals sections where all deletions in the `specifications.md` are listed
Literally copy the diff deletion into a bullet point for each deletion
Changes on subsequent lines of the same line number should be grouped together in the Features/Updates and Removals sections.

Commit the staged changes in the `specifications.md` file

After the commit, the task is completed.

Example workflow:

1. Run `git diff --cached specifications.md` to collect the changes in the file.

2. The specifications contains the following changes:
```
+Add a new section for data processing steps
```
3. Summary example: "Spec: Add a new section for data processing steps
4. Features/Updates section:
```
Features:
- Add a new section for data processing steps
```
5. Removals section:
```
Removals:
- None
```
6. Commit the changes with the message:
```
Spec: Add a new section for data processing steps
Features:
- Add a new section for data processing steps
Removals:
- None
```
7. Run `git commit -m "Spec: Add a new section for data processing steps
Features:
- Add a new section for data processing steps
Removals:
- None"` to commit the changes.