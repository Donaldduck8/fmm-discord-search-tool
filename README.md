# fmm-discord-search-tool

A small Python script to help exclude songs by duration on Soundcloud and Bandcamp. The tool first searches your query exhaustively (limited to 8000 results on Soundcloud and 500 results on Bandcamp by the API), then searches by duration locally.

Please note: Sometimes the Soundcloud client ID may expire. I'll try to find a way around this

## Setup
- Install Python 3
  - Make sure to check "Add to PATH" at the end of the installation
- Download and extract this repository to a folder
- Open a command prompt inside that folder
- Run ``python -m ensurepip``
- Run ``pip install -r requirements.txt``
- Run ``python fmm-discord-search-tool.py``

## Usage
This tool's first major accomplishment was helping to identify the unknown song "Just Don't Let It Go". I'll take you through that process step-by-step:

![](https://cdn.discordapp.com/attachments/580764088909692947/1019424049455169607/unknown.png)

The tool is controlled through direct input on the command-line. When faced with a menu, just type the number of the option you would like to select and press Enter. In this case, I selected Soundcloud, entered a search query of "Take My Hand", chose a duration and a genre. The tool will now exhaustively search that query on Soundcloud, which will take some time. Be patient!

![](https://cdn.discordapp.com/attachments/580764088909692947/1019424319262183445/unknown.png)

Still awake? Now that the tool has finished collecting the results, you can save them to a .json file that you can load again later, should you wish to refer back to these results. Now we're getting to the interesting part though: searching by duration.

![](https://cdn.discordapp.com/attachments/580764088909692947/1019424484521947176/unknown.png)

After selecting the corresponding menu option, you can enter either an exact duration, or a range with a minimum and maximum. The filtered results are then saved in a file called ``search_results.txt`` I recommend opening this file with Notepad++ because it allows you to double-click and automatically open any hyperlinks inside the file.

![](https://cdn.discordapp.com/attachments/580764088909692947/1019424645147013200/unknown.png)

![](https://cdn.discordapp.com/attachments/580764088909692947/1019424795395358760/unknown.png)

Inside this file are all the filtered results which you can now check one-by-one. They're (mostly) tabulated except for some weird unicode characters. This file will be overwritten if you do another filtered search, so make sure to save it elsewhere if you'd like to keep it!

![](https://cdn.discordapp.com/attachments/580764088909692947/1019424884033589398/unknown.png)

Ta-da! Good luck on your searches!
