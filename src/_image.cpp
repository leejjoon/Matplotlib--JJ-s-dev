
#include <iostream>
#include <fstream>
#include <cmath>
#include <cstdio>
#include <png.h>

#include "Python.h" //after png.h due to setjmp bug
#include <string>

#ifdef NUMARRAY
#include "numarray/arrayobject.h"
#else
#ifdef NUMERIC
#include "Numeric/arrayobject.h"
#else
#include "numpy/arrayobject.h"
#endif
#endif

#include "agg_pixfmt_rgb.h"
#include "agg_pixfmt_rgba.h"
#include "agg_color_rgba.h"
#include "agg_rendering_buffer.h"
#include "agg_rasterizer_scanline_aa.h"
#include "agg_scanline_bin.h"
#include "agg_path_storage.h"
#include "agg_conv_transform.h"
#include "agg_span_image_filter_rgb.h"
#include "agg_span_image_filter_rgba.h"
#include "agg_span_interpolator_linear.h"
#include "agg_scanline_bin.h"
#include "agg_scanline_u.h"
#include "agg_renderer_scanline.h"
#include "util/agg_color_conv_rgb8.h"
#include "_image.h"
#include "mplutils.h"



typedef agg::pixfmt_rgba32 pixfmt;
typedef agg::renderer_base<pixfmt> renderer_base;
typedef agg::span_interpolator_linear<> interpolator_type;
typedef agg::rasterizer_scanline_aa<> rasterizer;


Image::Image() :
  bufferIn(NULL), rbufIn(NULL), colsIn(0), rowsIn(0),
  bufferOut(NULL), rbufOut(NULL), colsOut(0), rowsOut(0),  BPP(4),
  interpolation(BILINEAR), aspect(ASPECT_FREE), bg(1,1,1,0) {
  _VERBOSE("Image::Image");
}

Image::~Image() {
  _VERBOSE("Image::~Image");
  delete [] bufferIn; bufferIn = NULL;
  delete rbufIn; rbufIn=NULL;
  delete rbufOut; rbufOut = NULL;
  delete [] bufferOut; bufferOut=NULL;
}

int
Image::setattr( const char * name, const Py::Object & value ) {
  _VERBOSE("Image::setattr");
  __dict__[name] = value;
  return 0;
}

Py::Object
Image::getattr( const char * name ) {
  _VERBOSE("Image::getattro");
  if ( __dict__.hasKey(name) ) return __dict__[name];
  else return getattr_default( name );

}

char Image::apply_rotation__doc__[] =
"apply_rotation(angle)\n"
"\n"
"Apply the rotation (degrees) to image"
;
Py::Object
Image::apply_rotation(const Py::Tuple& args) {
  _VERBOSE("Image::apply_rotation");

  args.verify_length(1);
  double r = Py::Float(args[0]);


  agg::trans_affine M = agg::trans_affine_rotation( r * agg::pi / 180.0);
  srcMatrix *= M;
  imageMatrix *= M;
  return Py::Object();
}



char Image::flipud_out__doc__[] =
"flipud()\n"
"\n"
"Flip the output image upside down"
;
Py::Object
Image::flipud_out(const Py::Tuple& args) {
  _VERBOSE("Image::flipud_out");

  args.verify_length(0);
  int stride = rbufOut->stride();
  rbufOut->attach(bufferOut, colsOut, rowsOut, -stride);
  return Py::Object();
}

char Image::flipud_in__doc__[] =
"flipud()\n"
"\n"
"Flip the input image upside down"
;
Py::Object
Image::flipud_in(const Py::Tuple& args) {
  _VERBOSE("Image::flipud_in");

  args.verify_length(0);
  int stride = rbufIn->stride();
  rbufIn->attach(bufferIn, colsIn, rowsIn, -stride);

  return Py::Object();
}

char Image::set_bg__doc__[] =
"set_bg(r,g,b,a)\n"
"\n"
"Set the background color"
;

Py::Object
Image::set_bg(const Py::Tuple& args) {
  _VERBOSE("Image::set_bg");

  args.verify_length(4);
  bg.r = Py::Float(args[0]);
  bg.g = Py::Float(args[1]);
  bg.b = Py::Float(args[2]);
  bg.a = Py::Float(args[3]);
  return Py::Object();
}

char Image::apply_scaling__doc__[] =
"apply_scaling(sx, sy)\n"
"\n"
"Apply the scale factors sx, sy to the transform matrix"
;

Py::Object
Image::apply_scaling(const Py::Tuple& args) {
  _VERBOSE("Image::apply_scaling");

  args.verify_length(2);
  double sx = Py::Float(args[0]);
  double sy = Py::Float(args[1]);

  //printf("applying scaling %1.2f, %1.2f\n", sx, sy);
  agg::trans_affine M = agg::trans_affine_scaling(sx, sy);
  srcMatrix *= M;
  imageMatrix *= M;

  return Py::Object();


}

char Image::apply_translation__doc__[] =
"apply_translation(tx, ty)\n"
"\n"
"Apply the translation tx, ty to the transform matrix"
;

Py::Object
Image::apply_translation(const Py::Tuple& args) {
  _VERBOSE("Image::apply_translation");

  args.verify_length(2);
  double tx = Py::Float(args[0]);
  double ty = Py::Float(args[1]);

  //printf("applying translation %1.2f, %1.2f\n", tx, ty);
  agg::trans_affine M = agg::trans_affine_translation(tx, ty);
  srcMatrix *= M;
  imageMatrix *= M;

  return Py::Object();


}

char Image::as_rgba_str__doc__[] =
"numrows, numcols, s = as_rgba_str()"
"\n"
"Call this function after resize to get the data as string\n"
"The string is a numrows by numcols x 4 (RGBA) unsigned char buffer\n"
;

Py::Object
Image::as_rgba_str(const Py::Tuple& args, const Py::Dict& kwargs) {
  _VERBOSE("Image::as_rgba_str");

  args.verify_length(0);

  std::pair<agg::int8u*,bool> bufpair = _get_output_buffer();

  Py::Object ret =  Py::asObject(Py_BuildValue("lls#", rowsOut, colsOut,
					       bufpair.first, colsOut*rowsOut*4));

  if (bufpair.second) delete [] bufpair.first;
  return ret;


}


char Image::buffer_argb32__doc__[] =
"buffer = buffer_argb32()"
"\n"
"Return the image buffer as agbr32\n"
;
Py::Object
Image::buffer_argb32(const Py::Tuple& args) {
  //"Return the image object as argb32";

  _VERBOSE("RendererAgg::buffer_argb32");

  args.verify_length(0);

  int row_len = colsOut * 4;

  unsigned char* buf_tmp = new unsigned char[row_len * rowsOut];
  if (buf_tmp ==NULL)
    throw Py::MemoryError("RendererAgg::buffer_argb32 could not allocate memory");

  agg::rendering_buffer rtmp;
  rtmp.attach(buf_tmp, colsOut, rowsOut, row_len);

  agg::color_conv(&rtmp, rbufOut, agg::color_conv_rgba32_to_argb32());

  //todo: how to do this with native CXX
  //PyObject* o = Py_BuildValue("s#", buf_tmp, row_len * rowsOut);
  PyObject* o = Py_BuildValue("lls#", rowsOut, colsOut,
			      buf_tmp, row_len * rowsOut);
  delete [] buf_tmp;
  return Py::asObject(o);


}


char Image::buffer_rgba__doc__[] =
"buffer = buffer_rgba()"
"\n"
"Return the image buffer as rgba32\n"
;
Py::Object
Image::buffer_rgba(const Py::Tuple& args) {
  //"Return the image object as rgba";

  _VERBOSE("RendererAgg::buffer_rgba");

  args.verify_length(0);
  int row_len = colsOut * 4;
  PyObject* o = Py_BuildValue("lls#", rowsOut, colsOut,
			      rbufOut, row_len * rowsOut);
  return Py::asObject(o);


}

char Image::reset_matrix__doc__[] =
"reset_matrix()"
"\n"
"Reset the transformation matrix"
;

Py::Object
Image::reset_matrix(const Py::Tuple& args) {
  _VERBOSE("Image::reset_matrix");

  args.verify_length(0);
  srcMatrix.reset();
  imageMatrix.reset();

  return Py::Object();


}

char Image::resize__doc__[] =
"resize(width, height, norm=1, radius=4.0)\n"
"\n"
"Resize the image to width, height using interpolation\n"
"norm and radius are optional args for some of the filters and must be\n"
"passed as kwargs\n"
;

Py::Object
Image::resize(const Py::Tuple& args, const Py::Dict& kwargs) {
  _VERBOSE("Image::resize");

  args.verify_length(2);

  int norm = 1;
  if ( kwargs.hasKey("norm") ) norm = Py::Int( kwargs["norm"] );

  double radius = 4.0;
  if ( kwargs.hasKey("radius") ) radius = Py::Float( kwargs["radius"] );

  if (bufferIn ==NULL)
    throw Py::RuntimeError("You must first load the image");

  int numcols = Py::Int(args[0]);
  int numrows = Py::Int(args[1]);

  colsOut = numcols;
  rowsOut = numrows;


  size_t NUMBYTES(numrows * numcols * BPP);

  delete [] bufferOut;
  bufferOut = new agg::int8u[NUMBYTES];
  if (bufferOut ==NULL) //todo: also handle allocation throw
    throw Py::MemoryError("Image::resize could not allocate memory");

  delete rbufOut;
  rbufOut = new agg::rendering_buffer;
  rbufOut->attach(bufferOut, numcols, numrows, numcols * BPP);

  // init the output rendering/rasterizing stuff
  pixfmt pixf(*rbufOut);
  renderer_base rb(pixf);
  rb.clear(bg);
  agg::rasterizer_scanline_aa<> ras;
  agg::scanline_u8 sl;


  //srcMatrix *= resizingMatrix;
  //imageMatrix *= resizingMatrix;
  imageMatrix.invert();
  interpolator_type interpolator(imageMatrix);

  agg::span_allocator<agg::rgba8> sa;
  agg::rgba8 background(agg::rgba8(int(255*bg.r),
				   int(255*bg.g),
				   int(255*bg.b),
				   int(255*bg.a)));




  // the image path
  agg::path_storage path;
  agg::int8u *bufferPad = NULL;
  agg::rendering_buffer rbufPad;

  double x0, y0, x1, y1;

  if (interpolation==NEAREST) {
    x0 = 0.0;
    x1 = colsIn;
    y0 = 0.0;
    y1 = rowsIn;
  }
  else {
    // if interpolation != nearest, create a new input buffer with the
    // edges mirrored on all size.  Then new buffer size is colsIn+2 by
    // rowsIn+2

    x0 = 1.0;
    x1 = colsIn+1;
    y0 = 1.0;
    y1 = rowsIn+1;


    bufferPad = new agg::int8u[(rowsIn+2) * (colsIn+2) * BPP];
    if (bufferPad ==NULL)
      throw Py::MemoryError("Image::resize could not allocate memory");
    rbufPad.attach(bufferPad, colsIn+2, rowsIn+2, (colsIn+2) * BPP);

    pixfmt pixfpad(rbufPad);
    renderer_base rbpad(pixfpad);

    pixfmt pixfin(*rbufIn);
    renderer_base rbin(pixfin);

    rbpad.copy_from(*rbufIn, 0, 1, 1);

    agg::rect_base<int> firstrow(0, 0, colsIn-1, 0);
    rbpad.copy_from(*rbufIn, &firstrow, 1, 0);

    agg::rect_base<int> lastrow(0, rowsIn-1, colsIn-1, rowsIn-1);
    rbpad.copy_from(*rbufIn, &lastrow, 1, 2);

    agg::rect_base<int> firstcol(0, 0, 0, rowsIn-1);
    rbpad.copy_from(*rbufIn, &firstcol, 0, 1);

    agg::rect_base<int> lastcol(colsIn-1, 0, colsIn-1, rowsIn-1);
    rbpad.copy_from(*rbufIn, &lastcol, 2, 1);

    rbpad.copy_pixel(0, 0, rbin.pixel(0,0) );
    rbpad.copy_pixel(0, colsIn+1, rbin.pixel(0,colsIn-1) );
    rbpad.copy_pixel(rowsIn+1, 0, rbin.pixel(rowsIn-1,0) );
    rbpad.copy_pixel(rowsIn+1, colsIn+1, rbin.pixel(rowsIn-1,colsIn-1) );


  }


  path.move_to(x0, y0);
  path.line_to(x1, y0);
  path.line_to(x1, y1);
  path.line_to(x0, y1);
  path.close_polygon();
  agg::conv_transform<agg::path_storage> imageBox(path, srcMatrix);
  ras.add_path(imageBox);

  switch(interpolation)
    {

    case NEAREST:
      {
	typedef agg::span_image_filter_rgba_nn<agg::rgba8,agg::order_rgba, interpolator_type> span_gen_type;
	typedef agg::renderer_scanline_aa<renderer_base, span_gen_type> renderer_type;

	span_gen_type sg(sa, *rbufIn, background, interpolator);
	renderer_type ri(rb, sg);
	agg::render_scanlines(ras, sl, ri);
      }
      break;
        case BILINEAR:
        case BICUBIC:
        case SPLINE16:
        case SPLINE36:
        case HANNING:
        case HAMMING:
        case HERMITE:
        case KAISER:
        case QUADRIC:
        case CATROM:
        case GAUSSIAN:
        case BESSEL:
        case MITCHELL:
        case SINC:
        case LANCZOS:
        case BLACKMAN:
            {
                agg::image_filter_lut filter;
                switch(interpolation)
                {
                case BILINEAR:  filter.calculate(agg::image_filter_bilinear(), norm); break;
                case BICUBIC:  filter.calculate(agg::image_filter_bicubic(), norm); break;
                case SPLINE16:  filter.calculate(agg::image_filter_spline16(), norm); break;
                case SPLINE36:  filter.calculate(agg::image_filter_spline36(), norm); break;
                case HANNING:  filter.calculate(agg::image_filter_hanning(), norm); break;
                case HAMMING:  filter.calculate(agg::image_filter_hamming(), norm); break;
                case HERMITE:  filter.calculate(agg::image_filter_hermite(), norm); break;
                case KAISER:  filter.calculate(agg::image_filter_kaiser(), norm); break;
                case QUADRIC:  filter.calculate(agg::image_filter_quadric(), norm); break;
                case CATROM: filter.calculate(agg::image_filter_catrom(), norm); break;
                case GAUSSIAN: filter.calculate(agg::image_filter_gaussian(), norm); break;
                case BESSEL: filter.calculate(agg::image_filter_bessel(), norm); break;
                case MITCHELL: filter.calculate(agg::image_filter_mitchell(), norm); break;
                case SINC: filter.calculate(agg::image_filter_sinc(radius), norm); break;
                case LANCZOS: filter.calculate(agg::image_filter_lanczos(radius), norm); break;
                case BLACKMAN: filter.calculate(agg::image_filter_blackman(radius), norm); break;
                }

	typedef agg::span_image_filter_rgba<agg::rgba8, agg::order_rgba,
	  interpolator_type> span_gen_type;
	typedef agg::renderer_scanline_aa<renderer_base, span_gen_type> renderer_type;
	span_gen_type sg(sa, rbufPad, background, interpolator, filter);
	renderer_type ri(rb, sg);
	agg::render_scanlines(ras, sl, ri);

      }
      break;

    }

  delete [] bufferPad;
  return Py::Object();

}



char Image::get_interpolation__doc__[] =
"get_interpolation()\n"
"\n"
"Get the interpolation scheme to one of the module constants, "
"one of image.NEAREST, image.BILINEAR, etc..."
;

Py::Object
Image::get_interpolation(const Py::Tuple& args) {
  _VERBOSE("Image::get_interpolation");

  args.verify_length(0);
  return Py::Int((int)interpolation);
}


char Image::get_aspect__doc__[] =
"get_aspect()\n"
"\n"
"Get the aspect constraint constants"
;

Py::Object
Image::get_aspect(const Py::Tuple& args) {
  _VERBOSE("Image::get_aspect");

  args.verify_length(0);
  return Py::Int((int)aspect);
}

char Image::get_size__doc__[] =
"numrows, numcols = get_size()\n"
"\n"
"Get the number or rows and columns of the input image"
;

Py::Object
Image::get_size(const Py::Tuple& args) {
  _VERBOSE("Image::get_size");

  args.verify_length(0);

  Py::Tuple ret(2);
  ret[0] = Py::Int((long)rowsIn);
  ret[1] = Py::Int((long)colsIn);
  return ret;

}

char Image::get_size_out__doc__[] =
"numrows, numcols = get_size()\n"
"\n"
"Get the number or rows and columns of the output image"
;

Py::Object
Image::get_size_out(const Py::Tuple& args) {
  _VERBOSE("Image::get_size");

  args.verify_length(0);

  Py::Tuple ret(2);
  ret[0] = Py::Int((long)rowsOut);
  ret[1] = Py::Int((long)colsOut);
  return ret;

}

//get the output buffer, flipped if necessary.  The second element of
//the pair is a bool that indicates whether you need to free the
//memory
std::pair<agg::int8u*, bool>
Image::_get_output_buffer() {
  _VERBOSE("Image::_get_output_buffer");
  std::pair<agg::int8u*, bool> ret;
  bool flipy = rbufOut->stride()<0;
  if (flipy) {
    agg::int8u* buffer = new agg::int8u[rowsOut*colsOut*4];
    agg::rendering_buffer rb;
    rb.attach(buffer, colsOut, rowsOut, colsOut*4);
    rb.copy_from(*rbufOut);
    ret.first = buffer;
    ret.second = true;
  }
  else {
    ret.first = bufferOut;
    ret.second = false;
  }
  return ret;

}


char Image::set_interpolation__doc__[] =
"set_interpolation(scheme)\n"
"\n"
"Set the interpolation scheme to one of the module constants, "
"eg, image.NEAREST, image.BILINEAR, etc..."
;

Py::Object
Image::set_interpolation(const Py::Tuple& args) {
  _VERBOSE("Image::set_interpolation");

  args.verify_length(1);

  size_t method = Py::Int(args[0]);
  interpolation = (unsigned)method;
  return Py::Object();

}



// this code is heavily adapted from the paint license, which is in
// the file paint.license (BSD compatible) included in this
// distribution.  TODO, add license file to MANIFEST.in and CVS
char Image::write_png__doc__[] =
"write_png(fname)\n"
"\n"
"Write the image to filename fname as png\n"
;
Py::Object
Image::write_png(const Py::Tuple& args)
{
  //small memory leak in this function - JDH 2004-06-08
  _VERBOSE("Image::write_png");

  args.verify_length(1);

  std::pair<agg::int8u*,bool> bufpair = _get_output_buffer();

  std::string fileName = Py::String(args[0]);
  const char *file_name = fileName.c_str();
  FILE *fp;
  png_structp png_ptr;
  png_infop info_ptr;
  struct        png_color_8_struct sig_bit;
  png_uint_32 row=0;

  //todo: allocate on heap
  png_bytep *row_pointers = new png_bytep[rowsOut];

  for (row = 0; row < rowsOut; ++row)
    row_pointers[row] = bufpair.first + row * colsOut * 4;

  fp = fopen(file_name, "wb");
  if (fp == NULL) {
    if (bufpair.second) delete [] bufpair.first;
    delete [] row_pointers;
    throw Py::RuntimeError(Printf("Could not open file %s", file_name).str());
  }


  png_ptr = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
  if (png_ptr == NULL) {
    if (bufpair.second) delete [] bufpair.first;
    fclose(fp);
    delete [] row_pointers;
    throw Py::RuntimeError("Could not create write struct");
  }

  info_ptr = png_create_info_struct(png_ptr);
  if (info_ptr == NULL) {
    if (bufpair.second) delete [] bufpair.first;
    fclose(fp);
    png_destroy_write_struct(&png_ptr, &info_ptr);
    delete [] row_pointers;
    throw Py::RuntimeError("Could not create info struct");
  }

  if (setjmp(png_ptr->jmpbuf)) {
    if (bufpair.second) delete [] bufpair.first;
    fclose(fp);
    png_destroy_write_struct(&png_ptr, &info_ptr);
    delete [] row_pointers;
    throw Py::RuntimeError("Error building image");
  }

  png_init_io(png_ptr, fp);
  png_set_IHDR(png_ptr, info_ptr,
	       colsOut, rowsOut, 8,
	       PNG_COLOR_TYPE_RGB_ALPHA, PNG_INTERLACE_NONE,
	       PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);

  // this a a color image!
  sig_bit.gray = 0;
  sig_bit.red = 8;
  sig_bit.green = 8;
  sig_bit.blue = 8;
  /* if the image has an alpha channel then */
  sig_bit.alpha = 8;
  png_set_sBIT(png_ptr, info_ptr, &sig_bit);

  png_write_info(png_ptr, info_ptr);
  png_write_image(png_ptr, row_pointers);
  png_write_end(png_ptr, info_ptr);
  png_destroy_write_struct(&png_ptr, &info_ptr);
  fclose(fp);

  delete [] row_pointers;

  if (bufpair.second) delete [] bufpair.first;
  return Py::Object();
}



char Image::set_aspect__doc__[] =
"set_aspect(scheme)\n"
"\n"
"Set the aspect ration to one of the image module constant."
"eg, one of image.ASPECT_PRESERVE, image.ASPECT_FREE"
;
Py::Object
Image::set_aspect(const Py::Tuple& args) {
  _VERBOSE("Image::set_aspect");

  args.verify_length(1);
  size_t method = Py::Int(args[0]);
  aspect = (unsigned)method;
  return Py::Object();

}

void
Image::init_type() {
  _VERBOSE("Image::init_type");

  behaviors().name("Image");
  behaviors().doc("Image");
  behaviors().supportGetattr();
  behaviors().supportSetattr();

  add_varargs_method( "apply_rotation", &Image::apply_rotation, Image::apply_rotation__doc__);
  add_varargs_method( "apply_scaling",	&Image::apply_scaling, Image::apply_scaling__doc__);
  add_varargs_method( "apply_translation", &Image::apply_translation, Image::apply_translation__doc__);
  add_keyword_method( "as_rgba_str", &Image::as_rgba_str, Image::as_rgba_str__doc__);
  add_varargs_method( "buffer_argb32", &Image::buffer_argb32, Image::buffer_argb32__doc__);
  add_varargs_method( "buffer_rgba", &Image::buffer_rgba, Image::buffer_rgba__doc__);
  add_varargs_method( "get_aspect", &Image::get_aspect, Image::get_aspect__doc__);
  add_varargs_method( "get_interpolation", &Image::get_interpolation, Image::get_interpolation__doc__);
  add_varargs_method( "get_size", &Image::get_size, Image::get_size__doc__);
  add_varargs_method( "get_size_out", &Image::get_size_out, Image::get_size_out__doc__);
  add_varargs_method( "reset_matrix", &Image::reset_matrix, Image::reset_matrix__doc__);
  add_keyword_method( "resize", &Image::resize, Image::resize__doc__);
  add_varargs_method( "set_interpolation", &Image::set_interpolation, Image::set_interpolation__doc__);
  add_varargs_method( "set_aspect", &Image::set_aspect, Image::set_aspect__doc__);
  add_varargs_method( "write_png", &Image::write_png, Image::write_png__doc__);
  add_varargs_method( "set_bg", &Image::set_bg, Image::set_bg__doc__);
  add_varargs_method( "flipud_out", &Image::flipud_out, Image::flipud_out__doc__);
  add_varargs_method( "flipud_in", &Image::flipud_in, Image::flipud_in__doc__);


}




char _image_module_from_images__doc__[] =
"from_images(numrows, numcols, seq)\n"
"\n"
"return an image instance with numrows, numcols from a seq of image\n"
"instances using alpha blending.  seq is a list of (Image, ox, oy)"
;
Py::Object
_image_module::from_images(const Py::Tuple& args) {
  _VERBOSE("_image_module::from_images");

  args.verify_length(3);

  size_t numrows = Py::Int(args[0]);
  size_t numcols = Py::Int(args[1]);

  Py::SeqBase<Py::Object> tups = args[2];
  size_t N = tups.length();

  if (N==0)
    throw Py::RuntimeError("Empty list of images");

  Py::Tuple tup;

  size_t ox(0), oy(0), thisx(0), thisy(0);

  //copy image 0 output buffer into return images output buffer
  Image* imo = new Image;
  imo->rowsOut  = numrows;
  imo->colsOut  = numcols;

  size_t NUMBYTES(numrows * numcols * imo->BPP);
  imo->bufferOut = new agg::int8u[NUMBYTES];
  if (imo->bufferOut==NULL) //todo: also handle allocation throw
    throw Py::MemoryError("_image_module::from_images could not allocate memory");

  delete imo->rbufOut;
  imo->rbufOut = new agg::rendering_buffer;
  imo->rbufOut->attach(imo->bufferOut, imo->colsOut, imo->rowsOut, imo->colsOut * imo->BPP);

  pixfmt pixf(*imo->rbufOut);
  renderer_base rb(pixf);


  for (size_t imnum=0; imnum< N; imnum++) {
    tup = Py::Tuple(tups[imnum]);
    Image* thisim = static_cast<Image*>(tup[0].ptr());
    if (imnum==0)
      rb.clear(thisim->bg);
    ox = Py::Int(tup[1]);
    oy = Py::Int(tup[2]);

    size_t ind=0;
    for (size_t j=0; j<thisim->rowsOut; j++) {
      for (size_t i=0; i<thisim->colsOut; i++) {
	thisx = i+ox;
	thisy = j+oy;
	if (thisx<0 || thisx>=numcols || thisy<0 || thisy>=numrows) {
	  ind +=4;
	  continue;
	}

	pixfmt::color_type p;
	p.r = *(thisim->bufferOut+ind++);
	p.g = *(thisim->bufferOut+ind++);
	p.b = *(thisim->bufferOut+ind++);
	p.a = *(thisim->bufferOut+ind++);
	pixf.blend_pixel(thisx, thisy, p, 255);
      }
    }
  }

  return Py::asObject(imo);



}



char _image_module_readpng__doc__[] =
"readpng(fname)\n"
"\n"
"Load an image from png file into a numerix array of MxNx4 uint8";
Py::Object
_image_module::readpng(const Py::Tuple& args) {

  args.verify_length(1);
  std::string fname = Py::String(args[0]);

  png_byte header[8];	// 8 is the maximum size that can be checked

  FILE *fp = fopen(fname.c_str(), "rb");
  if (!fp)
    throw Py::RuntimeError(Printf("_image_module::readpng could not open PNG file %s for reading", fname.c_str()).str());

  fread(header, 1, 8, fp);
  if (png_sig_cmp(header, 0, 8))
    throw Py::RuntimeError("_image_module::readpng: file not recognized as a PNG file");


  /* initialize stuff */
  png_structp png_ptr = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);

  if (!png_ptr)
    throw Py::RuntimeError("_image_module::readpng:  png_create_read_struct failed");

  png_infop info_ptr = png_create_info_struct(png_ptr);
  if (!info_ptr)
    throw Py::RuntimeError("_image_module::readpng:  png_create_info_struct failed");

  if (setjmp(png_jmpbuf(png_ptr)))
    throw Py::RuntimeError("_image_module::readpng:  error during init_io");

  png_init_io(png_ptr, fp);
  png_set_sig_bytes(png_ptr, 8);

  png_read_info(png_ptr, info_ptr);

  png_uint_32 width = info_ptr->width;
  png_uint_32 height = info_ptr->height;

  // convert misc color types to rgb for simplicity
  if (info_ptr->color_type == PNG_COLOR_TYPE_GRAY ||
      info_ptr->color_type == PNG_COLOR_TYPE_GRAY_ALPHA)
    png_set_gray_to_rgb(png_ptr);
  else if (info_ptr->color_type == PNG_COLOR_TYPE_PALETTE)
    png_set_palette_to_rgb(png_ptr);


  int bit_depth = info_ptr->bit_depth;
  if (bit_depth == 16)  png_set_strip_16(png_ptr);


  png_set_interlace_handling(png_ptr);
  png_read_update_info(png_ptr, info_ptr);

  bool rgba = info_ptr->color_type == PNG_COLOR_TYPE_RGBA;
  if ( (info_ptr->color_type != PNG_COLOR_TYPE_RGB) && !rgba) {
    std::cerr << "Found color type " << (int)info_ptr->color_type  << std::endl;
    throw Py::RuntimeError("_image_module::readpng: cannot handle color_type");
  }

  /* read file */
  if (setjmp(png_jmpbuf(png_ptr)))
    throw Py::RuntimeError("_image_module::readpng: error during read_image");

  png_bytep *row_pointers = new png_bytep[height];
  png_uint_32 row;

  for (row = 0; row < height; row++)
    row_pointers[row] = new png_byte[png_get_rowbytes(png_ptr,info_ptr)];

  png_read_image(png_ptr, row_pointers);



  int dimensions[3];
  dimensions[0] = height;  //numrows
  dimensions[1] = width;   //numcols
  dimensions[2] = 4;

  PyArrayObject *A = (PyArrayObject *) PyArray_FromDims(3, dimensions, PyArray_FLOAT);


  for (png_uint_32 y = 0; y < height; y++) {
    png_byte* row = row_pointers[y];
    for (png_uint_32 x = 0; x < width; x++) {

      png_byte* ptr = (rgba) ? &(row[x*4]) : &(row[x*3]);
      size_t offset = y*A->strides[0] + x*A->strides[1];
      //if ((y<10)&&(x==10)) std::cout << "r = " << ptr[0] << " " << ptr[0]/255.0 << std::endl;
      *(float*)(A->data + offset + 0*A->strides[2]) = ptr[0]/255.0;
      *(float*)(A->data + offset + 1*A->strides[2]) = ptr[1]/255.0;
      *(float*)(A->data + offset + 2*A->strides[2]) = ptr[2]/255.0;
      *(float*)(A->data + offset + 3*A->strides[2]) = rgba ? ptr[3]/255.0 : 1.0;
    }
  }

  //free the png memory
  png_read_end(png_ptr, info_ptr);
  png_destroy_read_struct(&png_ptr, &info_ptr, png_infopp_NULL);
  fclose(fp);
  for (row = 0; row < height; row++)
    delete [] row_pointers[row];
  delete [] row_pointers;
  return Py::asObject((PyObject*)A);
}


char _image_module_fromarray__doc__[] =
"fromarray(A, isoutput)\n"
"\n"
"Load the image from a Numeric or numarray array\n"
"By default this function fills the input buffer, which can subsequently\n"
"be resampled using resize.  If isoutput=1, fill the output buffer.\n"
"This is used to support raw pixel images w/o resampling"
;
Py::Object
_image_module::fromarray(const Py::Tuple& args) {
  _VERBOSE("_image_module::fromarray");

  args.verify_length(2);

  Py::Object x = args[0];
  int isoutput = Py::Int(args[1]);
  //PyArrayObject *A = (PyArrayObject *) PyArray_ContiguousFromObject(x.ptr(), PyArray_DOUBLE, 2, 3);
  PyArrayObject *A = (PyArrayObject *) PyArray_FromObject(x.ptr(), PyArray_DOUBLE, 2, 3);

  if (A==NULL)
    throw Py::ValueError("Array must be rank 2 or 3 of doubles");


  Image* imo = new Image;

  imo->rowsIn  = A->dimensions[0];
  imo->colsIn  = A->dimensions[1];


  size_t NUMBYTES(imo->colsIn * imo->rowsIn * imo->BPP);
  agg::int8u *buffer = new agg::int8u[NUMBYTES];
  if (buffer==NULL) //todo: also handle allocation throw
    throw Py::MemoryError("_image_module::fromarray could not allocate memory");

  if (isoutput) {
    // make the output buffer point to the input buffer

    imo->rowsOut  = imo->rowsIn;
    imo->colsOut  = imo->colsIn;

    imo->rbufOut = new agg::rendering_buffer;
    imo->bufferOut = buffer;
    imo->rbufOut->attach(imo->bufferOut, imo->colsOut, imo->rowsOut, imo->colsOut * imo->BPP);

  }
  else {
    imo->bufferIn = buffer;
    imo->rbufIn = new agg::rendering_buffer;
    imo->rbufIn->attach(buffer, imo->colsIn, imo->rowsIn, imo->colsIn*imo->BPP);
  }

  if   (A->nd == 2) { //assume luminance for now;

    agg::int8u gray;
    for (size_t rownum=0; rownum<imo->rowsIn; rownum++) {
     for (size_t colnum=0; colnum<imo->colsIn; colnum++) {
       double val = *(double *)(A->data + rownum*A->strides[0] + colnum*A->strides[1]);

       gray = int(255 * val);
       *buffer++ = gray;       // red
       *buffer++ = gray;       // green
       *buffer++ = gray;       // blue
       *buffer++   = 255;        // alpha
     }
    }
  }
  else if   (A->nd == 3) { // assume RGB

    if (A->dimensions[2] != 3 && A->dimensions[2] != 4 ) {
      Py_XDECREF(A);
      throw Py::ValueError(Printf("3rd dimension must be length 3 (RGB) or 4 (RGBA); found %d", A->dimensions[2]).str());

    }

    int rgba = A->dimensions[2]==4;
    double r,g,b,alpha;
    int offset =0;

    for (size_t rownum=0; rownum<imo->rowsIn; rownum++) {
      for (size_t colnum=0; colnum<imo->colsIn; colnum++) {
	offset = rownum*A->strides[0] + colnum*A->strides[1];
	r = *(double *)(A->data + offset);
	g = *(double *)(A->data + offset + A->strides[2] );
	b = *(double *)(A->data + offset + 2*A->strides[2] );

	if (rgba)
	  alpha = *(double *)(A->data + offset + 3*A->strides[2] );
	else
	  alpha = 1.0;

	*buffer++ = int(255*r);         // red
	*buffer++ = int(255*g);         // green
	*buffer++ = int(255*b);         // blue
	*buffer++ = int(255*alpha);     // alpha

      }
    }

  }
  else   { // error
    Py_XDECREF(A);
    throw Py::ValueError("Illegal array rank; must be rank; must 2 or 3");
  }
  buffer -= NUMBYTES;
  Py_XDECREF(A);

  return Py::asObject( imo );
}

char _image_module_fromarray2__doc__[] =
"fromarray2(A, isoutput)\n"
"\n"
"Load the image from a Numeric or numarray array\n"
"By default this function fills the input buffer, which can subsequently\n"
"be resampled using resize.  If isoutput=1, fill the output buffer.\n"
"This is used to support raw pixel images w/o resampling"
;
Py::Object
_image_module::fromarray2(const Py::Tuple& args) {
  _VERBOSE("_image_module::fromarray2");

  args.verify_length(2);

  Py::Object x = args[0];
  int isoutput = Py::Int(args[1]);
  PyArrayObject *A = (PyArrayObject *) PyArray_ContiguousFromObject(x.ptr(), PyArray_DOUBLE, 2, 3);
  //PyArrayObject *A = (PyArrayObject *) PyArray_FromObject(x.ptr(), PyArray_DOUBLE, 2, 3);

  if (A==NULL)
    throw Py::ValueError("Array must be rank 2 or 3 of doubles");


  Image* imo = new Image;

  imo->rowsIn  = A->dimensions[0];
  imo->colsIn  = A->dimensions[1];


  size_t NUMBYTES(imo->colsIn * imo->rowsIn * imo->BPP);
  agg::int8u *buffer = new agg::int8u[NUMBYTES];
  if (buffer==NULL) //todo: also handle allocation throw
    throw Py::MemoryError("_image_module::fromarray could not allocate memory");

  if (isoutput) {
    // make the output buffer point to the input buffer

    imo->rowsOut  = imo->rowsIn;
    imo->colsOut  = imo->colsIn;

    imo->rbufOut = new agg::rendering_buffer;
    imo->bufferOut = buffer;
    imo->rbufOut->attach(imo->bufferOut, imo->colsOut, imo->rowsOut, imo->colsOut * imo->BPP);

  }
  else {
    imo->bufferIn = buffer;
    imo->rbufIn = new agg::rendering_buffer;
    imo->rbufIn->attach(buffer, imo->colsIn, imo->rowsIn, imo->colsIn*imo->BPP);
  }

  if   (A->nd == 2) { //assume luminance for now;

    agg::int8u gray;
    const size_t N = imo->rowsIn * imo->colsIn;
    size_t i = 0;
    while (i++<N) {
      double val = *(double *)(A->data++);

      gray = int(255 * val);
      *buffer++ = gray;       // red
      *buffer++ = gray;       // green
      *buffer++ = gray;       // blue
      *buffer++   = 255;        // alpha
    }

  }
  else if   (A->nd == 3) { // assume RGB

    if (A->dimensions[2] != 3 && A->dimensions[2] != 4 ) {
      Py_XDECREF(A);
      throw Py::ValueError(Printf("3rd dimension must be length 3 (RGB) or 4 (RGBA); found %d", A->dimensions[2]).str());

    }

    int rgba = A->dimensions[2]==4;
    double r,g,b,alpha;
    const size_t N = imo->rowsIn * imo->colsIn;
    size_t i = 0;
    while (i<N) {
	r = *(double *)(A->data++);
	g = *(double *)(A->data++);
	b = *(double *)(A->data++);

	if (rgba)
	  alpha = *(double *)(A->data++);
	else
	  alpha = 1.0;

	*buffer++ = int(255*r);         // red
	*buffer++ = int(255*g);         // green
	*buffer++ = int(255*b);         // blue
	*buffer++ = int(255*alpha);     // alpha

      }

  }
  else   { // error
    Py_XDECREF(A);
    throw Py::ValueError("Illegal array rank; must be rank; must 2 or 3");
  }
  buffer -= NUMBYTES;
  Py_XDECREF(A);

  return Py::asObject( imo );
}

char _image_module_frombyte__doc__[] =
"frombyte(A, isoutput)\n"
"\n"
"Load the image from a byte array.\n"
"By default this function fills the input buffer, which can subsequently\n"
"be resampled using resize.  If isoutput=1, fill the output buffer.\n"
"This is used to support raw pixel images w/o resampling."
;
Py::Object
_image_module::frombyte(const Py::Tuple& args) {
  _VERBOSE("_image_module::frombyte");

  args.verify_length(2);

  Py::Object x = args[0];
  int isoutput = Py::Int(args[1]);

  PyArrayObject *A = (PyArrayObject *) PyArray_ContiguousFromObject(x.ptr(), PyArray_UBYTE, 3, 3);

  if (A->dimensions[2]<3 || A->dimensions[2]>4)
      throw Py::ValueError("Array dimension 3 must have size 3 or 4");

  Image* imo = new Image;

  imo->rowsIn = A->dimensions[0];
  imo->colsIn = A->dimensions[1];

  agg::int8u *arrbuf;
  agg::int8u *buffer;

  arrbuf = reinterpret_cast<agg::int8u *>(A->data);

  size_t NUMBYTES(imo->colsIn * imo->rowsIn * imo->BPP);
  buffer = new agg::int8u[NUMBYTES];

  if (buffer==NULL) //todo: also handle allocation throw
      throw Py::MemoryError("_image_module::frombyte could not allocate memory");

  const size_t N = imo->rowsIn * imo->colsIn * imo->BPP;
  size_t i = 0;
  if (A->dimensions[2] == 4) {
      memmove(buffer, arrbuf, N);
  } else {
      while (i < N) {
          memmove(buffer, arrbuf, 3);
          buffer += 3;
          arrbuf += 3;
          *buffer++ = 255;
          i += 4;
      }
      buffer -= N;
      arrbuf -= imo->rowsIn * imo->colsIn;
  }
  Py_XDECREF(A);

  if (isoutput) {
    // make the output buffer point to the input buffer

    imo->rowsOut  = imo->rowsIn;
    imo->colsOut  = imo->colsIn;

    imo->rbufOut = new agg::rendering_buffer;
    imo->bufferOut = buffer;
    imo->rbufOut->attach(imo->bufferOut, imo->colsOut, imo->rowsOut, imo->colsOut * imo->BPP);

  }
  else {
    imo->bufferIn = buffer;
    imo->rbufIn = new agg::rendering_buffer;
    imo->rbufIn->attach(buffer, imo->colsIn, imo->rowsIn, imo->colsIn*imo->BPP);
  }

  return Py::asObject( imo );
}

char _image_module_frombuffer__doc__[] =
"frombuffer(buffer, width, height, isoutput)\n"
"\n"
"Load the image from a character buffer\n"
"By default this function fills the input buffer, which can subsequently\n"
"be resampled using resize.  If isoutput=1, fill the output buffer.\n"
"This is used to support raw pixel images w/o resampling."
;
Py::Object
_image_module::frombuffer(const Py::Tuple& args) {
  _VERBOSE("_image_module::frombuffer");

  args.verify_length(4);

  PyObject *bufin = new_reference_to(args[0]);
  int x = Py::Int(args[1]);
  int y = Py::Int(args[2]);
  int isoutput = Py::Int(args[3]);

  if (PyObject_CheckReadBuffer(bufin) != 1)
    throw Py::ValueError("First argument must be a buffer.");

  Image* imo = new Image;

  imo->rowsIn = y;
  imo->colsIn = x;
  size_t NUMBYTES(imo->colsIn * imo->rowsIn * imo->BPP);

  int buflen;
  const agg::int8u *rawbuf;
  if (PyObject_AsReadBuffer(bufin, reinterpret_cast<const void**>(&rawbuf), &buflen) != 0)
    throw Py::ValueError("Cannot get buffer from object.");

  // Check buffer is required size.
  if ((size_t)buflen != NUMBYTES)
    throw Py::ValueError("Buffer length must be width * height * 4.");

  // Copy from input buffer to new buffer for agg.
  agg::int8u* buffer = new agg::int8u[NUMBYTES];
  if (buffer==NULL) //todo: also handle allocation throw
    throw Py::MemoryError("_image_module::frombuffer could not allocate memory");
  memmove(buffer, rawbuf, NUMBYTES);

  if (isoutput) {
    // make the output buffer point to the input buffer

    imo->rowsOut  = imo->rowsIn;
    imo->colsOut  = imo->colsIn;

    imo->rbufOut = new agg::rendering_buffer;
    imo->bufferOut = buffer;
    imo->rbufOut->attach(imo->bufferOut, imo->colsOut, imo->rowsOut, imo->colsOut * imo->BPP);

  }
  else {
    imo->bufferIn = buffer;
    imo->rbufIn = new agg::rendering_buffer;
    imo->rbufIn->attach(buffer, imo->colsIn, imo->rowsIn, imo->colsIn*imo->BPP);
  }

  return Py::asObject(imo); 
}


char __image_module_pcolor__doc__[] =
"pcolor(x, y, data, rows, cols, bounds)\n"
"\n"
"Generate a psudo-color image from data on a non-univorm grid using\n"
"nearest neighbour interpolation.\n"
"bounds = (x_min, x_max, y_min, y_max)\n"
;
Py::Object
_image_module::pcolor(const Py::Tuple& args) {
  _VERBOSE("_image_module::pcolor");


  if (args.length() != 6)
      throw Py::TypeError("Incorrect number of arguments (6 expected)");

  Py::Object xp = args[0];
  Py::Object yp = args[1];
  Py::Object dp = args[2];
  unsigned int rows = Py::Int(args[3]);
  unsigned int cols = Py::Int(args[4]);
  Py::Tuple bounds = args[5];

  if (bounds.length() !=4)
      throw Py::TypeError("Incorrect number of bounds (4 expected)");
  float x_min = Py::Float(bounds[0]);
  float x_max = Py::Float(bounds[1]);
  float y_min = Py::Float(bounds[2]);
  float y_max = Py::Float(bounds[3]);
  float width = x_max - x_min;
  float height = y_max - y_min;
  float dx = width / ((float) cols);
  float dy = height / ((float) rows);

  // Check we have something to output to
  if (rows == 0 || cols ==0)
      throw Py::ValueError("Cannot scale to zero size");

  // Get numeric arrays
  PyArrayObject *x = (PyArrayObject *) PyArray_ContiguousFromObject(xp.ptr(), PyArray_FLOAT, 1, 1);
  if (x == NULL)
      throw Py::ValueError("x is of incorrect type (wanted 1D float)");
  PyArrayObject *y = (PyArrayObject *) PyArray_ContiguousFromObject(yp.ptr(), PyArray_FLOAT, 1, 1);
  if (y == NULL) {
      Py_XDECREF(x);
      throw Py::ValueError("y is of incorrect type (wanted 1D float)");
  }
  PyArrayObject *d = (PyArrayObject *) PyArray_ContiguousFromObject(dp.ptr(), PyArray_UBYTE, 3, 3);
  if (d == NULL) {
      Py_XDECREF(x);
      Py_XDECREF(y);
      throw Py::ValueError("data is of incorrect type (wanted 3D UInt8)");
  }
  if (d->dimensions[2] != 4) {
      Py_XDECREF(x);
      Py_XDECREF(y);
      Py_XDECREF(d);
      throw Py::ValueError("data must be in RGBA format");
  }

  // Check dimensions match
  int nx = x->dimensions[0];
  int ny = y->dimensions[0];
  if (nx != d->dimensions[1] || ny != d->dimensions[0]) {
      Py_XDECREF(x);
      Py_XDECREF(y);
      Py_XDECREF(d);
      throw Py::ValueError("data and axis dimensions do not match");
  }

  // Allocate memory for pointer arrays
  unsigned int * rowstarts = reinterpret_cast<unsigned int*>(PyMem_Malloc(sizeof(unsigned int)*rows));
  if (rowstarts == NULL) {
      Py_XDECREF(x);
      Py_XDECREF(y);
      Py_XDECREF(d);
      throw Py::MemoryError("Cannot allocate memory for lookup table");
  }
  unsigned int * colstarts = reinterpret_cast<unsigned int*>(PyMem_Malloc(sizeof(unsigned int*)*cols));
  if (colstarts == NULL) {
      Py_XDECREF(x);
      Py_XDECREF(y);
      Py_XDECREF(d);
      PyMem_Free(rowstarts);
      throw Py::MemoryError("Cannot allocate memory for lookup table");
  }

  // Create output
  Image* imo = new Image;
  imo->rowsIn = rows;
  imo->rowsOut = rows;
  imo->colsIn = cols;
  imo->colsOut = cols;
  size_t NUMBYTES(rows * cols * 4);
  agg::int8u *buffer = new agg::int8u[NUMBYTES];
  if (buffer == NULL) {
      Py_XDECREF(x);
      Py_XDECREF(y);
      Py_XDECREF(d);
      PyMem_Free(rowstarts);
      PyMem_Free(colstarts);
      throw Py::MemoryError("Could not allocate memory for image");
  }

  // Calculate the pointer arrays to map input x to output x
  unsigned int i, j, j_last;
  unsigned int * colstart = colstarts;
  unsigned int * rowstart = rowstarts;
  float *xs1 = reinterpret_cast<float*>(x->data);
  float *ys1 = reinterpret_cast<float*>(y->data);
  float *xs2 = xs1+1;
  float *ys2 = ys1+1;
  float *xl = xs1 + nx - 1;
  float *yl = ys1 + ny - 1;
  float xo = x_min + dx/2.0;
  float yo = y_min + dy/2.0;
  float xm = 0.5*(*xs1 + *xs2);
  float ym = 0.5*(*ys1 + *ys2);
  // x/cols
  j = 0;
  j_last = j;
  for (i=0;i<cols;i++,xo+=dx,colstart++) {
      while(xs2 != xl && xo > xm) {
          xs1 = xs2;
          xs2 = xs1+1;
          xm = 0.5*(*xs1 + *xs2);
          j++;
      }
      *colstart = j - j_last;
      j_last = j;
  }
  // y/rows
  j = 0;
  j_last = j;
  for (i=0;i<rows;i++,yo+=dy,rowstart++) {
      while(ys2 != yl && yo > ym) {
          ys1 = ys2;
          ys2 = ys1+1;
          ym = 0.5*(*ys1 + *ys2);
          j++;
      }
      *rowstart = j - j_last;
      j_last = j;
  }


  // Copy data to output buffer
  unsigned char *start;
  unsigned char *inposition;
  size_t inrowsize(nx*4);
  size_t rowsize(cols*4);
  rowstart = rowstarts;
  agg::int8u * position = buffer;
  agg::int8u * oldposition = NULL;
  start = reinterpret_cast<unsigned char*>(d->data);
  for(i=0;i<rows;i++,rowstart++)
  {
      if (i > 0 && *rowstart == 0) {
          memcpy(position, oldposition, rowsize*sizeof(agg::int8u));
          oldposition = position;
          position += rowsize;
      } else {
          oldposition = position;
          start += *rowstart * inrowsize;
          inposition = start;
          for(j=0,colstart=colstarts;j<cols;j++,position+=4,colstart++) {
              inposition += *colstart * 4;
              memcpy(position, inposition, 4*sizeof(agg::int8u));
          }
      }
  }

  // Attatch output buffer to output buffer
  imo->rbufOut = new agg::rendering_buffer;
  imo->bufferOut = buffer;
  imo->rbufOut->attach(imo->bufferOut, imo->colsOut, imo->rowsOut, imo->colsOut * imo->BPP);

  Py_XDECREF(x);
  Py_XDECREF(y);
  Py_XDECREF(d);
  PyMem_Free(rowstarts);
  PyMem_Free(colstarts);

  return Py::asObject(imo);
}

#if defined(_MSC_VER)
DL_EXPORT(void)
#elif defined(__cplusplus)
  extern "C" void
#else
void
#endif

#ifdef NUMARRAY
init_na_image(void) {
  _VERBOSE("init_na_image");
#else
#   ifdef NUMERIC
  init_nc_image(void) {
    _VERBOSE("init_nc_image");
#   else
  init_ns_image(void) {
    _VERBOSE("init_ns_image");
#   endif
#endif

    static _image_module* _image = new _image_module;

    import_array();
    Py::Dict d = _image->moduleDictionary();

    d["NEAREST"] = Py::Int(Image::NEAREST);
    d["BILINEAR"] = Py::Int(Image::BILINEAR);
    d["BICUBIC"] = Py::Int(Image::BICUBIC);
    d["SPLINE16"] = Py::Int(Image::SPLINE16);
    d["SPLINE36"] = Py::Int(Image::SPLINE36);
    d["HANNING"] = Py::Int(Image::HANNING);
    d["HAMMING"] = Py::Int(Image::HAMMING);
    d["HERMITE"] = Py::Int(Image::HERMITE);
    d["KAISER"]   = Py::Int(Image::KAISER);
    d["QUADRIC"]   = Py::Int(Image::QUADRIC);
    d["CATROM"]  = Py::Int(Image::CATROM);
    d["GAUSSIAN"]  = Py::Int(Image::GAUSSIAN);
    d["BESSEL"]  = Py::Int(Image::BESSEL);
    d["MITCHELL"]  = Py::Int(Image::MITCHELL);
    d["SINC"]  = Py::Int(Image::SINC);
    d["LANCZOS"]  = Py::Int(Image::LANCZOS);
    d["BLACKMAN"] = Py::Int(Image::BLACKMAN);

    d["ASPECT_FREE"] = Py::Int(Image::ASPECT_FREE);
    d["ASPECT_PRESERVE"] = Py::Int(Image::ASPECT_PRESERVE);


  }




