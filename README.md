# raffle

This website implements a virtual version of the company raffle that we normally run as part of our annual Christmas party. 
In 2020 when we couldn't run it due to Covid-19, I put together a virtual version of it. 
At some point in the future, I may come back to this and productionise it in to a more general purpose solution so that other people can use it for running virtual raffles.

## TODO items:
 - Add tests
 - Tidy up API and split out functionality
 - Add user based admin functionality
 - Add reporting functionality
 - Chose a less resource intensive (ie long polling) based approach for the user updates
 
Known bugs:
 - There's an idempotency issue if people double click in quick succesion during the 'Normal Raffle' phase
 - Usernames are sorted lexicographically in the Swap gift drop down which can be counter intuitive when people have lower case names
 - The Gift chosen modal needs to resize and load before it displays
 - Once the Normal Raffle phase is over, we don't want the pop-up for 'XXX chose a gift' if someone navigates to the site
