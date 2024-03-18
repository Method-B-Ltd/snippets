Basic utility for moving messages from one M365 folder to another (including across mailbox) via EWS API, not MS 
Graph API. Use with caution, lots of rough edges.

Uses exchangelib 5.0.3 because of bug https://github.com/ecederstrand/exchangelib/issues/1222 - which appears to have 
since been fixed.