# Serverless 

# Serverless function local execution

stylist is able to execute your serverless python functions locally with some event and metrics logging. 

1. Execute lambda locally with event passed via command `stdin`

```bash
echo '{"text": "test", "channel": "test"}' | stylist serverless invoke slack_notify -
```

2. Execute lambda locally with custom event definition file

```bash
stylist serverless invoke slack_notify /tmp/event.json
```

3. Execute lambda locally with named event file
Stylist will look for event files in function subdirectory called `.events' and will try to find file named `<event_name>.json`


```bash
stylist serverless invoke slack_notify event_name
```
