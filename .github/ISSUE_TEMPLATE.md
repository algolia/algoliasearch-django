name: Bug Report
description: File a bug report.
title: '[bug]: '
labels: ['bug', 'triage']
body:
  - type: markdown
    attributes:
      value: |
        ## Please help us help you!

        Before filing your issue, ask yourself:
        - Is there an issue already opened for this bug?
        - Can I reproduce it?

        If you are not sure about the origin of the issue, or if it impacts your customer experience, please contact [our support team](https://alg.li/support).
  - type: textarea
    attributes:
      label: Description
      description: A clear and concise description of what the bug is.
    validations:
      required: true
  - type: dropdown
    id: python version
    attributes:
      label: python version
      description: What is the Python version you've reproduced the error with
      options:
        - 3.8
        - 3.9
        - 3.10
        - 3.11
        - 3.12
        - 3.13
    validations:
      required: true
  - type: dropdown
    id: django version
    attributes:
      label: Django version
      description: What is the Django version you've reproduced the error with
      options:
        - 4.0
        - 4.1
        - 4.2
        - 5.0
        - 5.1
    validations:
      required: true
  - type: textarea
    attributes:
      label: Steps to reproduce
      description: Write down the steps to reproduce the bug, please include any information that seems relevant for us to reproduce it properly
      placeholder: |
        1. Use method `...`
        2. With parameters `...`
        3. See error
    validations:
      required: true
  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      description: Please copy and paste any relevant log output. This will be automatically formatted into code, so no need for backticks.
      render: shell
  - type: checkboxes
    attributes:
      label: Self-service
      description: |
        If you feel like you could contribute to this issue, please check the box below. This would tell us and other people looking for contributions that someone's working on it.
        If you do check this box, please send a pull request within 7 days so we can still delegate this to someone else.
      options:
        - label: I'd be willing to fix this bug myself.

