- Currently steering/acceleration is too extreme. Need to put the division scale in the python script to a higher value to make it easier to make precise tilts
- Reduce emulator latency 

- Add play-rtp and boardcast-rtp code to impl chapter?
- Do testing and validation and update/uncomment section 5.7 accordingly?

- Add network latency and gather results. Basically do playability testing and add to eval chapter
- Write a complete host script
- Write a complete client script
- Add user manual/more professional README as an appendix

- Design trade offs section?
- Add a testing summary to appendix?
  
Questions for Tom:

- Do you have the other half of the feedback
- Can we do experiment
- I say that wii sport original had no online play. I knwo this is true but I cant find a source proving the negative. How can I source this/do I need to
- Is requirements table correct format?
- Should reference to figure 1.2 in design section be a duplication of the figure insetad?
- How can I do playability testing? I looked at the paper which talks about interaction lag which I might be able to measure but would be hard to get the latency between the wii performing the action and seeing the action over hdmi. Other than this what other playability testing can I do?
- Do I need a testing summary? 
- List of tables and list of figures?

Things to do:
- Do network analysis when artifical high ping?
- Too fluffy - too many weasel words
- Build on the figure over time
- More detail
- More citations?

- Delve into each objective in eval
- How limitations could be overcome
- Potential experiment - record tow screens one which goes through the whole thing (capture device, cables, network) and one that just has straight input from wii. Record both then press button. Check frame by frame for time difference
