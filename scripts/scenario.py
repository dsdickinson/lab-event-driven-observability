"""Controlled local incident scenarios. Run from the repository root."""
import os
import subprocess
import sys

SCENARIOS = {
    "baseline": "Resume services and clear injected failures",
    "api-down": "Stop the API so the blackbox probe fails",
    "slow-api": "Add 1.2 seconds to order creation",
    "fulfillment-backlog": "Stop the RabbitMQ worker while orders continue",
    "kafka-lag": "Stop the analytics consumer while events continue",
    "failed-fulfillment": "Force fulfillment tasks to fail and dead-letter",
}


def compose(*args, **env_updates):
    env = dict(os.environ)
    env.update(env_updates)
    subprocess.run(["docker", "compose", *args], check=True, env=env)


def main(name):
    if name == "baseline":
        compose("up", "-d", "--no-deps", "--force-recreate", "api", SLOW_API_MS="0")
        compose("up", "-d", "--no-deps", "--force-recreate", "worker", FAIL_FULFILLMENT="false")
        compose("up", "-d", "--no-deps", "analytics", "dispatcher", "traffic")
        compose("exec", "-T", "rabbitmq", "rabbitmqctl", "purge_queue", "fulfillment.dead")
    elif name == "api-down":
        compose("stop", "api")
    elif name == "slow-api":
        compose("up", "-d", "--no-deps", "--force-recreate", "api", SLOW_API_MS="1200")
    elif name == "fulfillment-backlog":
        compose("stop", "worker")
    elif name == "kafka-lag":
        compose("stop", "analytics")
    elif name == "failed-fulfillment":
        compose("up", "-d", "--no-deps", "--force-recreate", "worker", FAIL_FULFILLMENT="true")
    else:
        print("Usage: python3 scripts/scenario.py <name>\n")
        for key, description in SCENARIOS.items():
            print(f"  {key:22} {description}")
        return 2
    print(f"Scenario active: {name}. Run 'python3 scripts/scenario.py baseline' to reset.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
