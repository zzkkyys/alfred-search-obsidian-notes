-- Get the input parameter (vault name) passed from Python
on run argv
    -- First argument is the vault name
    set vaultName to item 1 of argv

    -- Construct the URL to open the vault
    set openVaultURL to "obsidian://open?vault=" & vaultName

    -- Open the URL using the default web browser
    do shell script "open " & quoted form of openVaultURL
end run
