# Alfred Obsidian Search Workflow

An Alfred Workflow for quick searching, previewing, and opening Obsidian notes.

## Features

- 🔍 Multi-vault search support
- 📝 Real-time Markdown preview
- 📊 Math formula rendering
- 🎨 Beautiful search results display
- ⚡ Fast response


## Requirements

- [Alfred 4+](https://www.alfredapp.com/)
- [Obsidian](https://obsidian.md/)
    - You must install the OmniSearch plugin, and open its HTTP server
    ![](https://ayyyyy.sbs/2025/10/52d20c2e3c2e31ea60df8f68f82041f9.png)
- Python packages
    - you have to install the following packages in your python environment
        ```bash
        pip install requests aiohttp aiofiles
        ```

## Installation

1. Download the latest `.alfredworkflow` file
2. Double-click to install in Alfred
3. Configure environment variables in Alfred preferences
![](https://ayyyyy.sbs/2025/10/8de508c68194d219385d9a526515e23d.png)
  - Configure Obsidian search ports in Alfred preferences
  - Configure python paths, use colon `:` to separate multiple paths if needed
4. Ensure Obsidian search service is running



## Usage

1. Press `⌥ + Space` to open Alfred
2. Type `obs` to trigger search
3. Enter search keywords
4. Use `⌘ + L` to preview search results
5. Press `Enter` to open file in Obsidian