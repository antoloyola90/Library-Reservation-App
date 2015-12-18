# A Developers Guide to the Reservation Galaxy

# Author

Anto Loyola

## Implementation Assumptions

- Resources can have the same name

- Resources can only have reservations on the same day

- In RSS, even the previous reservations that have passed are printed to help with book-keeping

- If an owner edits a resource then the reservations already on the system will not change and changes are made only for future reservations

- The Resource once created, cannot be deleted but can be changed to another resource. This functionality would be very easy to implement but I did not feel that I would learn anything new by implementing this. Concentrated on the extra credits instead 


## Extra Credit

- An Email will be sent out when the Reservation is made

- An Email will be sent out when the Reservation start time is 5 minutes away. This was implemented using a Cron Job.

- Resources can be searched by Name. Partial hits will also be shown. If no search value is given by the user then all resources are displayed

- Resources can be searched by Availability. Takes the Date, Start Time and the duration that the user is searching for. If duration is entered incorrectly by the user then duration = 1 hour.

- The number of times a resource has been reserved in the past is also shown wherever the resource is displayed

- Reservations cannot be made if there is already a reservation by the user for any resource during that time
