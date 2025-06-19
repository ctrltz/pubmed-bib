import click
import requests
import json
import re


# Get a reference from PubMed database
def get_reference(id):
    url_format = 'https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pubmed/'
    # Parameters for query
    queryParams = {
        'format': 'csl',
        'id': id
    }
    # get a reference
    response = requests.get(url_format, params = queryParams).json()
    return id, response


# Format the reference to BibTex format
def format_reference(reference, use_short):
    id, reference = reference
    title = reference['title'] if 'title' in reference.keys() else ''
    # convert <sub> and <sup>> to latex
    title = re.sub("<sub>(.+)</sub>", "$_{\\1}$", title)
    title = re.sub("<sup>(.+)</sup>", "$^{\\1}$", title)
    # wrap capital letters in curly brackets
    title = re.sub("([A-Z]+)", "{\\1}", title)

    authors = reference['author'] if 'author' in reference.keys() else ''
    authorList = []
    for author in authors:
        if ('family' in author.keys()) and ('given' in author.keys()):
            authorList.append(author['family'] + ', ' + author['given'])
        elif ('family' in author.keys()) and ('given' not in author.keys()):
            authorList.append(author['family'])
        elif ('family' not in author.keys()) and ('given' in author.keys()):
            authorList.append(author['given'])
        else:
            continue

    journal_long = reference.get('container-title') or ''
    journal_short = reference.get('container-title-short') or ''
    volume = reference.get('volume') or ''
    page = reference.get('page') or ''
    doi = reference.get('DOI', '')
    
    if 'issued' in reference.keys():
        year = reference['issued']['date-parts'][0][0]
    elif 'epub-date' in reference.keys():
        year = reference['epub-date']['date-parts'][0][0]    

    ref_id = authors[0]["family"].title() \
            if "family" in authors[0].keys() else authors[0]
    ref_id += str(year)

    output = f'''@article{{{ ref_id },
    title = {{{title}}},
    author = {{{' and '.join(authorList)}}},
    {"journal-long" if use_short else "journal"} = {{{journal_long}}},
    {"journal" if use_short else "journal-short"} = {{{journal_short}}},
    volume = {{{volume}}},
    pages = {{{page}}},
    year = {{{year}}},
    doi = {{{doi}}}
}}
'''
    return output


def show_reference(id, use_short):
    '''
    Get the BibTex styled reference from a given PMID from the PubMed database 
    using PubMed's API
    '''
    # Get the reference from PubMed
    reference = get_reference(id)
    # I the reference is not found
    if 'status' in reference[1].keys() and reference[1]['status'] == 'error' :
        output = 'Reference not found'
    else:
        output = format_reference(reference, use_short)

    click.echo(output)
    return


def save_reference(id, path, use_short):
    '''
    Append a reference to an bib file
    '''
    reference = get_reference(id)
    if 'status' in reference[1].keys() and reference[1]['status'] == 'error' :
        click.echo("Reference not found")
        return
    with open(path, "a") as f:
        f.write(format_reference(reference, use_short))
    return
        

def convert_references(input_file, output_file):
    # Read all PMIDs in
    id = []
    successNumber, failNumber = 0, 0
    with open(input_file) as ih:
        with open(output_file, 'w') as oh:
            for line in ih:
                ref = get_reference(line.rstrip())
                if 'status' in ref.keys() and ref['status'] == 'error' :
                    print(f'PMID {line.rstrip()} NOT FOUND')
                    failNumber += 1
                else: 
                    ref = format_reference(ref)
                    successNumber += 1
                    oh.write(ref+'\n')
    print(f'{successNumber} reference{"s" if successNumber > 1 else ""} ' +\
          f'retrieved.\n{failNumber} reference' +\
          f'{"s" if failNumber > 1 else ""} ' +\
          f'not found.')
    return

@click.command()
@click.option('--id', default=None,  help="The PubMed PMID.")
@click.option('--input-file', default=None,
              help='A text file with list of PMID')
@click.option('--output-file', default=None,
              help='The output file to store BibTex styled references')
@click.option('--short-journal/--long-journal', default=False,
              help="Use short journal name")
def pubMed2BibTex(id, input_file, output_file, short_journal):
    '''
    Retrieve article reference from PubMed in BibTex format.
    '''
    if id:
        if output_file:
            save_reference(id, output_file, short_journal)
        else:
            show_reference(id, short_journal)
    elif input_file and output_file:
        convert_references(input_file, output_file, short_journal)
    else:
        return

if __name__ == '__main__':
    pubMed2BibTex()