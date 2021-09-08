def apply_filter(array, filter_fn):
  filtered_array = []
  for item in array:
    try:
      if(filter_fn(item)):
        filtered_array.append(item)
    except TypeError as exc:
      raise Exception('An error occured while filtering:\n', exc)
    except KeyError as exc:
      raise Exception(f'The {exc} key does not exist for the item you are filtering')
  
  return filtered_array
