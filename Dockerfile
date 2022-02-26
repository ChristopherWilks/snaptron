FROM quay.io/broadsword/snaptron_base:1.0.1

# the actual Snaptron will be git cloned in the externally mounted "/deploy"
ADD . /snaptron/

# Make Snaptron ports available to the world outside this container
EXPOSE 1556 1557 1558 1585 1587 1590 1591 1592 1593 1594 1595

# Define environment variable
ENV NAME World

ENTRYPOINT ["/snaptron/entrypoint.sh"]
