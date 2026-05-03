## Overview

The following graph visualizes the steps it takes to render the dashboard view and map view user interfaces of the application.

![Application rendering graph](/images/front-end/rendering-overview.png)

Initializing the Mapbox map object is executed in the `mapStore`, while all other steps are executed by the `contentStore`.

## Map Layers

The following graph visualizes the steps it takes to render geographical data of a component to the map.

![Map rendering graph](/images/front-end/rendering-map.png)

All steps are executed by the `mapStore`.
