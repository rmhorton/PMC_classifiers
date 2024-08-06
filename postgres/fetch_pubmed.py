#! /home/rmhorton/anaconda3/envs/nlp/bin/python

# download the current baseline distribution of pubmed to the current directory.

import ftputil, os, re
import io, hashlib, hmac

host_address = 'ftp.ncbi.nlm.nih.gov'
target_path = '/pubmed/baseline/'

def verify_md5(gz_file, local_dir='/data/pubmed', verbose=False):
    md5_file = os.path.join(local_dir, gz_file + '.md5')

    try:
        with open(md5_file, "rt") as fmd5:
            their_md5 = fmd5.readline().split('=')[1].strip()
            if verbose: print(their_md5)

        with open(os.path.join(local_dir, gz_file), "rb") as fgz:
            my_md5 = hashlib.file_digest(fgz, "md5").hexdigest()
            if verbose: print(my_md5)
        
        return my_md5 == their_md5
    except:
        if verbose: print("Problem reading a file")
        return False


# Which files do we already have?
gotem = { f for f in os.listdir() if os.path.isfile(f) }  # re.search(r'\.xml\.gz', f)


# Download the ones we don't already have
print("Downloading missing files:")
with ftputil.FTPHost(host_address, 'anonymous', 'cybertory@gmail.com') as host:
    host.chdir(target_path)
    names = host.listdir(host.curdir)
    for name in names:
        if host.path.isfile(name) and name not in gotem:
            print('fetching', name)
            try:
            	host.download(name, name) # remote name, local name
            except:
            	print("Well, that didn't work.")


# Check signatures
print("Checking for failed files:")
failed_files = []
for f in [f for f in os.listdir("/data/pubmed") if f.endswith('.gz')]:
    if not verify_md5(f):
        print(f, 'FAILED')
        failed_files.append(f)
        os.rename(f, f"{f}.FAILED")
        # delete the corresponding MD5 file if it exists
        md5_file = f + '.md5'
        try:
	    os.remove(md5_file)
	except OSError:
	    pass

        
        
if len(failed_files) > 0:
    print("The following files failed:\n", failed_files)
    print("Re-run this script to try getting the failed files again.")
