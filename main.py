import os
import sys
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
import VTFLibWrapper.VTFLib as VTFLib
import VTFLibWrapper.VTFLibEnums as VTFLibEnums
from PIL import Image
from numpy import asarray, uint8
from ctypes import create_string_buffer

vtf_lib = VTFLib.VTFLib()

STICKER_W_MAX = 512
STICKER_H_MAX = 512

def export_texture(texture, path, imageFormat=None): # Exports an image to VTF using VTFLib
    image_data = (asarray(texture)*-1) * 255
    image_data = image_data.astype(uint8, copy=False)
    def_options = vtf_lib.create_default_params_structure()
    if imageFormat.startswith('RGBA8888'):
        def_options.ImageFormat = VTFLibEnums.ImageFormat.ImageFormatRGBA8888
        def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha
        if imageFormat == 'RGBA8888Normal':
            def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagNormal
    elif imageFormat.startswith('DXT1'):
        def_options.ImageFormat = VTFLibEnums.ImageFormat.ImageFormatDXT1
        if imageFormat == 'DXT1Normal':
            def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagNormal
    elif imageFormat.startswith('DXT5'):
        def_options.ImageFormat = VTFLibEnums.ImageFormat.ImageFormatDXT5
        def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha
        if imageFormat == 'DXT5Normal':
            def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagNormal
    else:
        def_options.ImageFormat = VTFLibEnums.ImageFormat.ImageFormatRGBA8888
        def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha

    def_options.Resize = 1
    w, h = texture.size

    image_data = create_string_buffer(image_data.tobytes())
    vtf_lib.image_create_single(w, h, image_data, def_options)
    vtf_lib.image_save(path)
    vtf_lib.image_destroy()

app = QApplication(sys.argv)

# Prompt the user to enter a name for the sticker pack
sticker_pack_name, ok = QInputDialog.getText(None, "Enter Sticker Pack Name", "Enter a name for the sticker pack:")
if not ok:
    sys.exit()

ok_sticker_pack_name = sticker_pack_name.replace(" ", "_")
ok_sticker_pack_name = ok_sticker_pack_name.lower()

author_name, ok = QInputDialog.getText(None, "Enter Author Name", "Enter a name for the author:")
if not ok:
    sys.exit()

# Open a file selection dialog
images, _ = QFileDialog.getOpenFileNames(None, "Select Images", "", "Images (*.png *.xpm *.jpg *.bmp);;All Files (*)")

# Create the materials directory for the sticker pack
materials_dir = "./project_{}/materials/stickers/{}/".format(ok_sticker_pack_name, ok_sticker_pack_name)
if not os.path.exists(materials_dir):
    os.makedirs(materials_dir)

lua_dir = "./project_{}/lua/arc9/common/attachments_bulk/".format(ok_sticker_pack_name)
if not os.path.exists(lua_dir):
    os.makedirs(lua_dir)

lua_file = open(lua_dir + "a9sm_{}.lua".format(ok_sticker_pack_name), "w")

lua_file.write("local ATT\n\n")

# Process each selected image
for image in images:
    # Prompt the user to enter a title for the image
    title, ok = QInputDialog.getText(None, "Enter Title for {}".format(image), "Enter Title for {}".format(image))
    if not ok:
        break

    oktitle = title.replace(" ", "_")
    # Remove ALL non-alphanumerics
    oktitle = ''.join(e for e in oktitle if e.isalnum())
    oktitle = oktitle.lower()

    # Prompt the user to enter a description for the image
    description, ok = QInputDialog.getText(None, "Enter Description for {}".format(image), "Enter Description for {}".format(image))
    if not ok:
        break

    imageTexture = Image.open(image)
    imageTexture = imageTexture.convert("RGBA")

    # Check if the image is too large, auto resize

    if imageTexture.size[0] > STICKER_W_MAX or imageTexture.size[1] > STICKER_H_MAX:
        if imageTexture.size[0] > imageTexture.size[1]:
            newWidth = STICKER_W_MAX
            newHeight = int(imageTexture.size[1] * (STICKER_W_MAX / imageTexture.size[0]))
        else:
            newWidth = int(imageTexture.size[0] * (STICKER_H_MAX / imageTexture.size[1]))
            newHeight = STICKER_H_MAX
        imageTexture = imageTexture.resize((newWidth, newHeight), Image.Resampling.LANCZOS)

    # Create the VTF and VMT file names based on the image title
    vtf_filename = "{}.vtf".format(oktitle)
    vmt_filename = "{}.vmt".format(oktitle)

    # Check if the VTF and VMT files already exist for this title
    vtf_exists = os.path.exists(os.path.join(materials_dir, vtf_filename))
    vmt_exists = os.path.exists(os.path.join(materials_dir, vmt_filename))

    # If the VTF and VMT files already exist, append a number to the file names
    i = 1
    while vtf_exists or vmt_exists:
        vtf_filename = "{}_{}.vtf".format(oktitle, i)
        vmt_filename = "{}_{}.vmt".format(oktitle, i)
        vtf_exists = os.path.exists(os.path.join(materials_dir, vtf_filename))
        vmt_exists = os.path.exists(os.path.join(materials_dir, vmt_filename))
        i += 1

    export_texture(imageTexture, os.path.join(materials_dir, vtf_filename), 'DXT5')

    # Strip the ".vtf" extension from the VTF file name
    vtf_name = os.path.splitext(vtf_filename)[0]

    # Create the material directory path
    material_dir_path = os.path.join("stickers", ok_sticker_pack_name, vtf_name)

    # Create the VMT file contents
    vmt_contents = """// This file was automatically generated by Arctic's Sticker Pack Creator
    VertexLitGeneric
    {{
        "$basetexture" "{}"
        "$alphatest"	"1"
        "$decal"		"1"
        "$nocull"		"1"
    }}""".format(material_dir_path, vtf_filename)

    # Write the VMT contents to a file
    with open(os.path.join(materials_dir, vmt_filename), "w") as f:
        f.write(vmt_contents)

    # In material_dir_path replace all backslashes with forward slashes

    material_dir_path = material_dir_path.replace("\\", "/")

    # Generate the code block for the current sticker
    code_block = """ATT = {{}}

ATT.PrintName = "{}"
ATT.CompactName = "{}"
ATT.Description = [[{}\nDesign by {}.\n\nSticker included in {}.]]
ATT.Icon = Material("{}")

ATT.Free = true

ATT.Category = "stickers"
ATT.Folder = "{}"

ATT.StickerMaterial = "{}"

ARC9.LoadAttachment(ATT, "sticker_{}_{}")\n""".format(
        title,
        oktitle.upper(),
        description,
        author_name,
        sticker_pack_name,
        material_dir_path,
        sticker_pack_name,
        material_dir_path,
        ok_sticker_pack_name,
        oktitle
    )

    # Write the code block to the Lua file
    lua_file.write(code_block)

lua_file.close()
sys.exit(app.exec_())