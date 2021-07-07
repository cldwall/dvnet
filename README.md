# A Network Virtualization Tool Based on Docker

# Running Tests
    python3 -m unittest tests/<test_file.py>

# Running the Program
    cd src/
    python3 -m docker_virt_net <path-to-net-conf>

# Fun Facts
Redefining an object key `hides' the previous occurrence. Thus a *JSON* file containing:

```json
{
    "S": {
        "fw_rules": {},
        "subnets": ["A", "B"]
    },
    "S": {
        "fw_rules": {},
        "subnets": ["A"]
    }
}
```

Would be ``translated'' into the following dictionary when loaded:

```python
{
    "S": {
        "fw_rules": {},
        "subnets": ["A"]
    }
}
```
