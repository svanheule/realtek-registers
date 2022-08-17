# What is this?

This repository tracks scripts to generate a database of Realtek CPU switch registers.

This database backs @svanheule's Realtek register web-databases, found e.g.:

- https://svanheule.net/realtek/cypress/
- https://svanheule.net/realtek/maple/
- https://svanheule.net/realtek/longan/
- https://svanheule.net/realtek/mango/

(See https://svanheule.net/realtek/ directly for the this list.)

## Building the database

`data-prosessing/run-all.sh` should extract the tables from a Realtek source archive. At the time of writing it only supports switch core register headers, and not other peripherals.

## Caveats

The only register info that is listed on https://svanheule.net/realtek/ is the switch core register space.  The other CPU peripherals (e.g. GPIO, timers) are at a different base address, and not available on the register website. For those registers, we still need to dive into the code archives to read the actual code, consult the (unstructured) wiki, or have personal documentation.

## Help improve this

The documentation website is underpowered/missing some information.

The website (https://svanheule.net/realtek) is written with python and flask. With some manual intervention, you too can get a copy running.

It could be nice if some improvements could be made:

- Better database structure to allow for

  - easier addition of more register ranges

  - describing peripherals

  - many-to-many mapping of peripherals with platforms so as to avoid repetition for identical peripherals

    A number of the CPU peripherals are present on all SoC generations with identical register spaces, but are at different address offsets, or even exist in different amounts if they are present multiple times (timers). Currently, things are ordered in a strict hierarchy, grouped by chip generation (maple, cypress, etc.).

- Better queries to speed up generation of the "recent changes".

## Talk to us!

You can find us on:

- IRC (#rtl83xx on libera.chat)
