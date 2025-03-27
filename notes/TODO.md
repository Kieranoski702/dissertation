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

- Is requirements table correct format?
- Should reference to figure 1.2 in design section be a duplication of the figure insetad?
- How can I do playability testing? I looked at the paper which talks about interaction lag which I might be able to measure but would be hard to get the latency between the wii performing the action and seeing the action over hdmi. Other than this what other playability testing can I do?
- Do I need a testing summary? 

Things to do:
- Too fluffy - too many weasel words
- Build on the figure over time
- More detail
- More citations?

- Delve into each objective in eval
- How limitations could be overcome
- Potential experiment - record tow screens one which goes through the whole thing (capture device, cables, network) and one that just has straight input from wii. Record both then press button. Check frame by frame for time difference
