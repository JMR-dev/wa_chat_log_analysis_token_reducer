
import argparse
import emoji

def reduce_tokens(input_file, output_file):
    """
    Reduces the number of tokens in a chat log file by replacing usernames and converting emojis.

    Args:
        input_file (str): The path to the input chat log file.
        output_file (str): The path to the output file.
    """
    with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            # Replace usernames
            line = line.replace('Honeybelle Ong-Jimenez Gaitano', 'Belle')
            line = line.replace('Jason Ross', 'Jason')

            # Convert emojis to text
            line = emoji.demojize(line)

            f_out.write(line)

def main():
    """
    Parses command-line arguments and calls the reduce_tokens function.
    """
    parser = argparse.ArgumentParser(description='Reduce the number of tokens in a chat log file.')
    parser.add_argument('input_file', help='The path to the input chat log file.')
    args = parser.parse_args()

    input_file = args.input_file
    output_file = input_file.rsplit('.', 1)[0] + '_redacted.txt'

    reduce_tokens(input_file, output_file)
    print(f'Successfully processed {input_file} and saved the result to {output_file}')

if __name__ == '__main__':
    main()
