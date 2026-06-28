import io
import zstandard as zstd
import oead
import byml
from utils import log

class SplatoonPackManager:
    def __init__(self):
        self.pack_path = None
        self.sarc = None
        self.byml_files = {}

    def load_pack(self, path):
        log(f"[ENGINE] Request to load archive: {path}")
        self.pack_path = path
        
        try:
            with open(path, 'rb') as f:
                compressed_data = f.read()

            dctx = zstd.ZstdDecompressor()
            decompressed_sarc_data = dctx.decompress(compressed_data)
            self.sarc = oead.Sarc(decompressed_sarc_data)
            
            self.byml_files.clear()
            count = 0
            
            for file in self.sarc.get_files():
                if file.name.endswith(".bgyml"):
                    try:
                        raw_bytes = bytes(file.data)
                        parser = byml.Byml(raw_bytes)
                        self.byml_files[file.name] = parser.parse()
                        count += 1
                    except Exception as e:
                        log(f"❌ [ENGINE] BGYML parsing error on {file.name}: {e}")
            
            log(f"[ENGINE] ✅ ZSTD/SARC archive successfully loaded: {count} BGYML v4+ stored in memory.")
            return True, "Archive loaded."
        except Exception as e:
            log(f"❌ [ENGINE] Critical load failure: {e}")
            return False, str(e)

    def save_pack(self, new_path):
        log(f"[ENGINE] Request to REPACK archive to: {new_path}")
        try:
            sarc_writer = oead.SarcWriter.from_sarc(self.sarc)
            
            for file_name, byml_data in self.byml_files.items():
                stream = io.BytesIO()
                writer = byml.Writer(byml_data, be=False, version=4)
                writer.write(stream)
                sarc_writer.files[file_name] = stream.getvalue()

            new_sarc_data = sarc_writer.write()[1]
            log("[ENGINE] ZSTD compression level 10 in progress...")
            cctx = zstd.ZstdCompressor(level=10)
            compressed_data = cctx.compress(new_sarc_data)

            with open(new_path, 'wb') as f:
                f.write(compressed_data)
                
            log(f"[ENGINE] ✅ REPACK finished and physically saved to disk.")
            return True, "File saved."
        except Exception as e:
            log(f"❌ [ENGINE] Critical REPACK failure: {e}")
            return False, str(e)