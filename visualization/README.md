# Visualization
To visualize the data (in this example sequence 00):
```sh
$ ./visualize.py -d /path/to/dataset/ -s 00
```

To visualize the predictions (in this example sequence 00):

```sh
$ ./visualize.py -d /path/to/dataset/ -p /path/to/predictions/ -s 00
```

If you want to visualize axis aligned bounding boxes use flag -b or --bboxes (in this example sequence 00):

```sh
$ ./visualize.py -d /path/to/dataset/ -p /path/to/predictions/ -s 00 -b
```

If you want to visualize region of interest use flag -r or --roi_filter (in this example sequence 00):

```sh
$ ./visualize.py -d /path/to/dataset/ -p /path/to/predictions/ -s 00 -r
```
