# Custom Streaming Dashboard 
> Dec. 16, 2024: Very nearly put this project on hiatus because no API can provide me with the information I desire to create a dashboard that is much different from streaming stat-trackers that already exist. Customizing Streamlit AgGrids has also proven to be tediously difficult. Will keep going at it for the time being tho.

(I will hopefully come up with a more creative name later on)

### Proposed Direction
A dashboard that analyses Spotify listening habits. There are lots of websites that do this, obviously, but it'd be nice to have a proper *dashboard*. I think I may do this for myself first, but a main goal is to be able to actually implement proper Spotify authentication ([video tutorial](https://www.youtube.com/watch?v=olY_2MW4Eik&ab_channel=ImdadCodes)).
* Features: 
    * You listened to x (unique) songs today, y (unique) artists
    * Most popular/obscure songs/artists
    * Line graph showing trends
    * Artist distribution donut charts (consult Spotify Slug)
    * What you've listened to so far this week - so last.fm and airbuds have something similar, except they do it for thelast 7 days. I don't want that. I want Monday to Sunday. Like what you've listened to this week *so far*. Just my preference.
* If I truly didn't want to go to the trouble of doing Spotify authentication, I believe last.fm has an API I can look into, which could be easier or harder than the actual authentication. 
* May or may not end up promoting this. Might just be a little something that I use for myself, because other websites don't satisfy me.

---
### Other misc. ideas
* In the summary tab, display total time (minutes/hours/days) listened since the user authenticated. Not sure how to track this continuously if the user logs out but surely there is some possible way