angou\_bitfinex 2 (May 24, 2018)
===
- `angou_bitfinex.rest` now exposes a module-scoped `LOGGER` variable, instead of
  per-class `angou_bitfinex.rest.RestSession.logger`s.
- If a response has a “success” HTTP status code but its body cannot be parsed
  as JSON, `angou_bitfinex.rest.InvalidJSON` is raised.
- `angou_bitfinex.rest.RestSession` constructor now takes an optional `timeout`
  argument.
- Fixed an error when called `angou_bitfinex.rest.RestV1Session.call_auth` with
  `params=None`.

angou\_bitfinex 1 (May 19, 2018)
===
The first release of angou\_bitfinex!
