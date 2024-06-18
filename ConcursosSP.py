import requests
from bs4 import BeautifulSoup
import re
import time
import folium
from datetime import datetime
import os





# Function to fetch the webpage content
def fetch_webpage(url):
    """Fetch the content of the webpage."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching webpage: {e}")
        return None

# Function to extract information between start_word and end_word
def extract_info(html, start_word, end_word):
    """Extract and return content between start_word and end_word."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()

        start_index = text.find(start_word)
        if start_index == -1:
            print(f"Start word '{start_word}' not found.")
            return None

        end_index = text.find(end_word, start_index)
        if end_index == -1:
            print(f"End word '{end_word}' not found.")
            return None

        # Extract the content between start and end words
        extracted_text = text[start_index:end_index + len(end_word)]
        return extracted_text
    except Exception as e:
        print(f"An error occurred during extraction: {e}")
        return None

# Function to process extracted text into dictionaries
def process_extracted_text(extracted_text):
    """Process the extracted text and store it in a dictionary."""
    try:
        lines = extracted_text.split('\n')
        data_dict = {}
        extra_info_dict = {}
        key_index = 0

        for i in range(len(lines)):
            if "SP" in lines[i]:
                # Key is the organization name and "RS"
                key = lines[i - 1].strip() + "\n" + lines[i].strip()
                # Value is the line before, the "RS" line, and the next two lines after "RS"
                value = "\n".join(lines[i - 2:i + 3]).strip()
                data_dict[key_index] = value
                extra_info_dict[key_index] = {
                    "extra_info_1": lines[i - 2].strip(),
                    "extra_info_2": lines[i + 1].strip(),
                    "extra_info_3": lines[i + 2].strip()
                }
                key_index += 1

        return data_dict, extra_info_dict
    except Exception as e:
        print(f"An error occurred during processing extracted text: {e}")
        return None, None

# Function to search for institution's address using its name online and get CEP from Google search
def search_address_by_name(name):
    try:
        # Search on Google
        url = f"https://www.google.com/search?q=o CEP de é {name}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract the CEP pattern from the search results
        cep_pattern = re.compile(r'\b\d{5}-\d{3}\b')
        # Find all elements matching the CEP pattern
        cep_elements = soup.find_all(string=cep_pattern)

        # Return the first CEP found
        for cep_element in cep_elements:
            if re.search(cep_pattern, cep_element):
                cep = re.search(cep_pattern, cep_element).group(0)
                return cep.strip()

        print(f"CEP not found for {name}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while searching for CEP: {e}")
        return None
    except Exception as e:
        print(f"An error occurred during CEP search: {e}")
        return None

# Function to get coordinates using Nominatim API
def get_coordinates_nominatim(address):
    """Get the coordinates of the address using Nominatim API."""
    if not address:
        return None

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json'
    }
    headers = {
        'User-Agent': 'YourAppName/1.0 (your@email.com)'  # Replace with your app name and contact email
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data:
            latitude = data[0]['lat']
            longitude = data[0]['lon']
            return latitude, longitude
        else:

            return None

    except Exception as e:
        print(f"An error occurred during the Nominatim geocoding: {e}")
        return None

# Function to get coordinates using OpenCage API
def get_coordinates_opencage(address, api_key):
    """Get the coordinates of the address using OpenCage API."""
    if not address:
        return None

    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        'q': address,
        'key': api_key
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            latitude = data['results'][0]['geometry']['lat']
            longitude = data['results'][0]['geometry']['lng']
            return latitude, longitude
        else:

            return None

    except Exception as e:
        print(f"An error occurred during the OpenCage geocoding: {e}")
        return None

# Function to get coordinates using Google Maps Geocoding API
def get_coordinates_google(address, api_key):
    """Get the coordinates of the address using Google Maps Geocoding API."""
    if not address:
        return None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': api_key
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'OK' and data['results']:
            latitude = data['results'][0]['geometry']['location']['lat']
            longitude = data['results'][0]['geometry']['location']['lng']
            return latitude, longitude
        else:

            return None

    except Exception as e:
        print(f"An error occurred during the Google Maps geocoding: {e}")
        return None

# Function to get coordinates using HERE Geocoding and Search API
def get_coordinates_here(address, api_key):
    """Get the coordinates of the address using HERE Geocoding and Search API."""
    if not address:
        return None

    url = "https://geocode.search.hereapi.com/v1/geocode"
    params = {
        'q': address,
        'apiKey': api_key
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'items' in data and data['items']:
            latitude = data['items'][0]['position']['lat']
            longitude = data['items'][0]['position']['lng']
            return latitude, longitude
        else:

            return None

    except Exception as e:
        print(f"An error occurred during the HERE geocoding: {e}")
        return None

# Function to get coordinates from CEP using a specific API
def get_coordinates_from_cep(cep):
    try:
        url = f"http://viacep.com.br/ws/{cep}/json/"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'erro' in data:
            print(f"No coordinates found for CEP: {cep}")
            return None

        if 'localidade' in data:
            city_name = data['localidade']
            return get_coordinates_from_city(city_name)
        else:
            print("City name ('localidade') not found in CEP data.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while getting coordinates from CEP: {e}")
        return None
    except ValueError as e:
        print(f"Invalid CEP format: {e}")
        return None
    except Exception as e:
        print(f"An error occurred during CEP to coordinates conversion: {e}")
        return None

# Function to get coordinates from city name using a specific API
# Function to get coordinates from city name using a specific API
def get_coordinates_from_city(city_name):
    try:
        url = 'https://api.api-ninjas.com/v1/geocoding?city={}'.format(city_name)
        response = requests.get(url, headers={'X-Api-Key': '7t5NdmoYx9evPA9a+64N3g==efKDpYxeN0ZcBHj2'})
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            # Iterate over the list to find the first entry with latitude and longitude
            for entry in data:
                if 'latitude' in entry and 'longitude' in entry:
                    latitude = entry['latitude']
                    longitude = entry['longitude']
                    return latitude, longitude
            print(f"No coordinates found for city: {city_name}")
            return None
        else:
            print(f"Unexpected response format for city: {city_name}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while getting coordinates from city: {e}")
        return None
    except Exception as e:
        print(f"An error occurred during city to coordinates conversion: {e}")
        return None

# Function to check if coordinates are within the geographical boundaries of Rio Grande do Sul
def is_within_rs(lat, lon):
    """Check if the coordinates are within the geographical boundaries of Rio Grande do Sul."""
    return -24.0 <= lat <= -20.0 and -54.0 <= lon <= -44.0

if __name__ == "__main__":
    # URL of the website to scrape
    url = "https://www.pciconcursos.com.br/professores/"

    # Your OpenCage, Google Maps, and HERE API keys (replace with your actual keys)
    opencage_api_key = "353694dd10e64eefab7f42b9564fb84c"
    google_api_key = "xfxW2FEj6GIaEz8dVfdAUr6oyuE"
    here_api_key = "r78cPffminYNEW7VgCRpsYld-6_kJOvFLaxWxT80aHg"

    # Fetch the webpage content
    html_content = fetch_webpage(url)
    if html_content is None:
        exit()

    # Extract information between "RIO GRANDE DO SUL" and "SANTA CATARINA"
    extracted_text = extract_info(html_content, "SÃO PAULO", "MINAS GERAIS")
    if extracted_text is None:
        exit()

    # Process extracted text into dictionaries
    data_dict, extra_info_dict = process_extracted_text(extracted_text)
    if not data_dict or not extra_info_dict:
        exit()

    found_count = 0
    not_found_count = 0
    institution_coordinates = {}
    not_found_list = []
    out_of_boundary_list = []  # New list for institutions out of boundary

    # Lists to count how many were found with each method
    found_with_nominatim = 0
    found_with_opencage = 0
    found_with_google = 0
    found_with_here = 0
    found_with_cep = 0

    start_time = time.time()  # Start time tracking

    # Loop through each institution in data_dict
    for key, value in data_dict.items():
        first_line = value.split('\n')[0]
        print(f"Searching for: {first_line}")

        coordinates = None
        method_tried = None

        # Attempt to get coordinates using geocoding APIs with fallback to CEP lookup
        if not coordinates:
            # Try Nominatim
            coordinates = get_coordinates_nominatim(first_line)
            method_tried = "Nominatim"
            if coordinates:
                found_with_nominatim += 1
            else:
                print(f"Coordinates not found using {method_tried} for: {first_line}")

        if not coordinates:
            # Try OpenCage
            coordinates = get_coordinates_opencage(first_line, opencage_api_key)
            method_tried = "OpenCage"
            if coordinates:
                found_with_opencage += 1
            else:
                print(f"Coordinates not found using {method_tried} for: {first_line}")

        if not coordinates:
            # Try Google Maps
            coordinates = get_coordinates_google(first_line, google_api_key)
            method_tried = "Google Maps"
            if coordinates:
                found_with_google += 1
            else:
                print(f"Coordinates not found using {method_tried} for: {first_line}")

        if not coordinates:
            # Try HERE
            coordinates = get_coordinates_here(first_line, here_api_key)
            method_tried = "HERE"
            if coordinates:
                found_with_here += 1
            else:
                print(f"Coordinates not found using {method_tried} for: {first_line}")
        if not coordinates:
            # Try CEP lookup
            print(f"Running CEP lookup for: {first_line}")
            cep = search_address_by_name(first_line)
            if cep:
                coordinates = get_coordinates_from_cep(cep)
                method_tried = "CEP Lookup"
                if coordinates:
                    found_with_cep += 1
                    print(f"Found coordinates using CEP lookup for {first_line}: {coordinates}")
                    institution_coordinates[first_line] = {
                        "coordinates": coordinates,
                        "info": extra_info_dict[key]
                    }
                    # Remove from out of boundary list if found
                    if first_line in out_of_boundary_list:
                        out_of_boundary_list.remove(first_line)
                else:
                    print(f"Coordinates not found using {method_tried} for: {first_line}")
            else:
                print(f"CEP not found for {first_line}")


        if coordinates:
            try:
                lat, lon = float(coordinates[0]), float(coordinates[1])
                if is_within_rs(lat, lon):
                    found_count += 1
                    print(f"Found: {first_line} -> Coordinates: {coordinates}")
                    institution_coordinates[first_line] = {
                        "coordinates": coordinates,
                        "info": extra_info_dict[key]
                    }
                else:
                    not_found_count += 1
                    print(f"Coordinates out of bounds for: {first_line}")
                    out_of_boundary_list.append(first_line)
                    # Run CEP lookup
                    print(f"Running CEP lookup for: {first_line}")
                    cep = search_address_by_name(first_line)
                    if cep:
                        coordinates = get_coordinates_from_cep(cep)
                        method_tried = "CEP Lookup"
                        if coordinates:
                            found_with_cep += 1
                            print(f"Found coordinates using CEP lookup for {first_line}: {coordinates}")
                            institution_coordinates[first_line] = {
                                "coordinates": coordinates,
                                "info": extra_info_dict[key]
                            }
                            # Remove from out of boundary list if found
                            out_of_boundary_list.remove(first_line)
                        else:
                            print(f"Coordinates not found using {method_tried} for: {first_line}")
                    else:
                        print(f"CEP not found for {first_line}")

            except (IndexError, ValueError) as e:
                print(f"Error processing coordinates for {first_line}: {e}")
                not_found_count += 1
                not_found_list.append(first_line)
        else:
            not_found_count += 1
            print(f"Not found: {first_line}")
            not_found_list.append(first_line)

        time.sleep(1)  # Sleep to avoid overwhelming the servers

    end_time = time.time()  # End time tracking
    elapsed_time = end_time - start_time  # Calculate elapsed time

    print(f"\nSummary:")

    print(f"Addresses not found: {not_found_count}")
    print(f"Elapsed time: {elapsed_time} seconds")

    map_center = [-30.0, -53.0]  # Approximate center of Rio Grande do Sul
    folium_map = folium.Map(location=map_center, zoom_start=7)

    for institution, details in institution_coordinates.items():
        try:
            lat, lon = float(details["coordinates"][0]), float(details["coordinates"][1])
            popup_content = f"""
            <b>{institution}</b><br>
            Instituição: {details["info"]["extra_info_1"]}<br>
            Vagas: {details["info"]["extra_info_2"]}<br>
            Prazo inscrição: {details["info"]["extra_info_3"]}
            """
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(folium_map)
        except (IndexError, ValueError) as e:
            not_found_list.append(institution)

    # Create the not found list as an HTML unordered list
    for institution, details in institution_coordinates.items():
        try:
            lat, lon = float(details["coordinates"][0]), float(details["coordinates"][1])
            popup_content = f"""
            <b>{institution}</b><br>
            Instituição: {details["info"]["extra_info_1"]}<br>
            Vagas: {details["info"]["extra_info_2"]}<br>
            Prazo inscrição: {details["info"]["extra_info_3"]}
            """
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(folium_map)
        except (IndexError, ValueError) as e:
            not_found_list.append(institution)
    for institution, details in institution_coordinates.items():
        try:
            lat, lon = float(details["coordinates"][0]), float(details["coordinates"][1])
            popup_content = f"""
            <b>{institution}</b><br>
            Instituição: {details["info"]["extra_info_1"]}<br>
            Vagas: {details["info"]["extra_info_2"]}<br>
            Prazo inscrição: {details["info"]["extra_info_3"]}
            """
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(folium_map)
        except (IndexError, ValueError) as e:
            not_found_list.append(institution)
    not_found_html = '<h4>Coordinates not found:</h4><ul>'
    for institution in not_found_list:
        if institution in extra_info_dict:
            info = extra_info_dict[institution]
            not_found_html += f'''
            <li><b>{institution}</b>: {info["extra_info_1"]} - {info["extra_info_2"]} - {info["extra_info_3"]}</li>
            '''
        else:
            not_found_html += f'<li>{institution}</li>'
    not_found_html += '</ul>'
    current_date = datetime.now().strftime("%d/%m/%Y")
    # Create the title HTML with the current date
    title_html = f"""
    <div style="text-align: center; font-family: Arial, sans-serif;">
        <h1>Concursos Para Professor</h1>
        <h3 style="color: gray;">Gerado em: {current_date}</h3>
    </div>
    """
    folium_map.get_root().html.add_child(folium.Element(title_html))
    button_html = f"""
    <div id="notFoundButton" style="position: fixed; top: 10px; right: 10px; z-index: 1000;">
        <button onclick="document.getElementById('notFoundList').style.display = 
        document.getElementById('notFoundList').style.display === 'none' ? 'block' : 'none';">
            Show/Hide Not Found List
        </button>
    </div>
    <div id="notFoundList" style="display: none; background-color: white; border: 1px solid black; padding: 10px; max-width: 300px; max-height: 300px; overflow-y: auto; position: fixed; top: 50px; right: 10px; z-index: 1000;">
        {not_found_html}
    </div>
    """

    # Add the button to the map
    folium_map.get_root().html.add_child(folium.Element(button_html))

    # Save the map to an HTML file
    map_filename = "/home/ec2-user/concurso2024/map_of_institutions.html"
    folium_map.save(map_filename)
    print(f"Map saved as {map_filename}")

    # Print summary of institutions not found
    if not_found_list:
        print("\nInstitutions not found:")
        for institution in not_found_list:
            print(institution)
    # Print summary of institutions out of boundary
    if out_of_boundary_list:
        print("\nInstitutions out of boundary (not within Rio Grande do Sul):")
        for institution in out_of_boundary_list:
            print(institution)

    # Additional summary
    print(f"Institutions found within Rio Grande do Sul: {found_count}")
    print(f"Institutions not found or out of boundary: {not_found_count + len(out_of_boundary_list)}")


    print(f"Found with Nominatim: {found_with_nominatim}")
    print(f"Found with OpenCage: {found_with_opencage}")
    print(f"Found with Google Maps: {found_with_google}")
    print(f"Found with HERE: {found_with_here}")
    print(f"Found with CEP Lookup: {found_with_cep}")

    # Save the not found and out of boundary institutions to files
    with open('not_found_institutions.txt', 'w') as f:
        f.write('\n'.join(not_found_list))

    with open('out_of_boundary_institutions.txt', 'w') as f:
        f.write('\n'.join(out_of_boundary_list))

    print("\nFiles for not found and out of boundary institutions saved.")

    # Open the map in the default web browser
    import webbrowser
    webbrowser.open('file://' + map_filename)








