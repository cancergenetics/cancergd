/**
	The missing SVG.toDataURL library for your SVG elements.
	
	Usage: SVGElement.toDataURL( type, { options } )

	Returns: the data URL, except when using native PNG renderer (needs callback).

	type	MIME type of the exported data.
			Default: image/svg+xml.
			Must support: image/png.
			Additional: image/jpeg.

	options is a map of options: {
		callback: function(dataURL)
			Callback function which is called when the data URL is ready.
			This is only necessary when using native PNG renderer.
			Default: undefined.
		
		[the rest of the options only apply when type="image/png" or type="image/jpeg"]

		renderer: "native"|"canvg"
			PNG renderer to use. Native renderer¹ might cause a security exception.
			Default: canvg if available, otherwise native.

		keepNonSafe: true|false
			Export non-safe (image and foreignObject) elements.
			This will set the Canvas origin-clean property to false, if this data is transferred to Canvas.
			Default: false, to keep origin-clean true.
			NOTE: not currently supported and is just ignored.

		keepOutsideViewport: true|false
			Export all drawn content, even if not visible.
			Default: false, export only visible viewport, similar to Canvas toDataURL().
			NOTE: only supported with canvg renderer.
	}

	See original paper¹ for more info on SVG to Canvas exporting.

	¹ http://svgopen.org/2010/papers/62-From_SVG_to_Canvas_and_Back/#svg_to_canvas
*/

SVGElement.prototype.toDataURL = function(type, options) {
	var _svg = this;
	
	function debug(s) {
		console.log("SVG.toDataURL:", s);
	}

	function exportSVG() {
		var svg_xml = XMLSerialize(_svg);
		var svg_dataurl = base64dataURLencode(svg_xml);
		debug(type + " length: " + svg_dataurl.length);

		// NOTE double data carrier
		if (options.callback) options.callback(svg_dataurl);
		return svg_dataurl;
	}

	function XMLSerialize(svg) {

		// quick-n-serialize an SVG dom, needed for IE9 where there's no XMLSerializer nor SVG.xml
		// s: SVG dom, which is the <svg> elemennt
		function XMLSerializerForIE(s) {
			var out = "";
			
			out += "<" + s.nodeName;
			for (var n = 0; n < s.attributes.length; n++) {
				out += " " + s.attributes[n].name + "=" + "'" + s.attributes[n].value + "'";
			}
			
			if (s.hasChildNodes()) {
				out += ">\n";

				for (var n = 0; n < s.childNodes.length; n++) {
					out += XMLSerializerForIE(s.childNodes[n]);
				}

				out += "</" + s.nodeName + ">" + "\n";

			} else out += " />\n";

			return out;
		}

		
		if (window.XMLSerializer) {
			debug("using standard XMLSerializer.serializeToString")
			return (new XMLSerializer()).serializeToString(svg);
		} else {
			debug("using custom XMLSerializerForIE")
			return XMLSerializerForIE(svg);
		}
	
	}

	function base64dataURLencode(s) {
		var b64 = "data:image/svg+xml;base64,";

		// https://developer.mozilla.org/en/DOM/window.btoa
		if (window.btoa) {
			debug("using window.btoa for base64 encoding");
			b64 += btoa(s);
		} else {
			debug("using custom base64 encoder");
			b64 += Base64.encode(s);
		}
		
		return b64;
	}

	
    function image_onload_timeout(canvas,ctx,svg_img,type) {  // SJB
			debug("exported image size: " + [svg_img.width, svg_img.height])			
			canvas.width = svg_img.width;
			canvas.height = svg_img.height;

			try {		
				ctx.drawImage(svg_img, 0, 0);  // Throws error in IE 11 (and other IEs): http://stackoverflow.com/questions/24346090/drawimage-raises-script65535-on-ie11
				// and: https://connect.microsoft.com/IE/feedback/details/809823/draw-svg-image-on-canvas-context		
			} catch (e) {
				// So could try again:
				//           setTimeout(function() {context.drawImage(image, 0, 0)}, 1);
				// setTimeout(function() {drawPiece(ctx,x,y,type,color)}, 1);
				alert("Error: Internet explorer has issues converting SVG to PNG images. Try using another webbrowser, such as Firefox, Opera, Chrome or Safari")
			}
			// Will see if the IE update fixes this: https://www.microsoft.com/en-us/download/details.aspx?id=51031

			// SECURITY_ERR WILL HAPPEN NOW
			if (type=="canvas") {
				if (options.callback) options.callback( canvas );
			    else debug("WARNING: no callback set, so nothing happens.");
			}
			else {		
			  try {  // SJB added this try .... catch based on idea from 'saveSVGAsPng.js'
				var png_dataurl = canvas.toDataURL(type);
				debug(type + " length: " + png_dataurl.length);
			  } catch (e) {
				if ((typeof SecurityError !== 'undefined' && e instanceof SecurityError) || e.name == "SecurityError") {
				console.error("Rendered SVG images cannot be downloaded in this browser.");
				alert('Rendered SVG to PNG images cannot be downloaded using this button in this browser, due to an issue with the browser\'s "canvas.toDataURL()" function.\n\nInstead if you are using Internet Explorer: with mouse pointer on the boxplot image, click the RIGHT mouse button, then from the popup menu choose "Save picture as...", then in the save dialog that appears, for the "Save as type" choose "PNG (*.png)", then "Save". If that doesn\'t work, then then try Firefox, Opera, Chrome or Safari browsers.');
				return;
				} else {
					throw e;
				}
			  }
				
			  if (options.callback) options.callback( png_dataurl );
			  else debug("WARNING: no callback set, so nothing happens.");
			}  
    }
	
	
	function exportImage(type) {
		var canvas = document.createElement("canvas");
		var ctx = canvas.getContext('2d');

		// TODO: if (options.keepOutsideViewport), do some translation magic?

		var svg_img = new Image();
		var svg_xml = XMLSerialize(_svg);
		svg_img.src = base64dataURLencode(svg_xml);

		svg_img.onload = function() {
		    setTimeout(function() {image_onload_timeout(canvas,ctx,svg_img,type);}, 50); // SJB: To try to overcome the error in IE 
		}
		
		svg_img.onerror = function() {
			console.log(
				"Can't export! Maybe your browser doesn't support " +
				"SVG in img element or SVG input for Canvas drawImage?\n" +
				"http://en.wikipedia.org/wiki/SVG#Native_support"
			);
		}

		// NOTE: will not return anything
	}

	function exportImageCanvg(type) {
		var canvas = document.createElement("canvas");
		var ctx = canvas.getContext('2d');
		var svg_xml = XMLSerialize(_svg);

		// NOTE: canvg gets the SVG element dimensions incorrectly if not specified as attributes
		//debug("detected svg dimensions " + [_svg.clientWidth, _svg.clientHeight])
		//debug("canvas dimensions " + [canvas.width, canvas.height])

		var keepBB = options.keepOutsideViewport;
		if (keepBB) var bb = _svg.getBBox();

		// NOTE: this canvg call is synchronous and blocks
		canvg(canvas, svg_xml, { 
			ignoreMouse: true, ignoreAnimation: true,
			offsetX: keepBB ? -bb.x : undefined, 
			offsetY: keepBB ? -bb.y : undefined,
			scaleWidth: keepBB ? bb.width+bb.x : undefined,
			scaleHeight: keepBB ? bb.height+bb.y : undefined,
			renderCallback: function() {
				debug("exported image dimensions " + [canvas.width, canvas.height]);
				if (type=="canvas") // Added by SJB
					if (options.callback) options.callback( canvas );
				else {
				var png_dataurl = canvas.toDataURL(type);
				debug(type + " length: " + png_dataurl.length);
				if (options.callback) options.callback( png_dataurl );
				}
			}
		});

		// NOTE: return in addition to callback
		return type=="canvas" ? canvas : canvas.toDataURL(type);
	}

	// BEGIN MAIN

	if (!type) type = "image/svg+xml";
	if (!options) options = {};

	if (options.keepNonSafe) debug("NOTE: keepNonSafe is NOT supported and will be ignored!");
	if (options.keepOutsideViewport) debug("NOTE: keepOutsideViewport is only supported with canvg exporter.");
	
	switch (type) {
		case "image/svg+xml":
			return exportSVG();
			break;

		case "image/png":
		case "image/jpeg":
		case "canvas": // Added by SJB, as IE can convert the returned canvas to a Blob (whereas todataURL can't be downloaded in IE using download)
			if (!options.renderer) {
				if (window.canvg) options.renderer = "canvg";
				else options.renderer="native";
			}

			switch (options.renderer) {
				case "canvg":
					debug("using canvg renderer for png export");
					return exportImageCanvg(type);
					break;

				case "native":
					debug("using native renderer for png export. THIS MIGHT FAIL.");
					return exportImage(type);
					break;

				default:
					debug("unknown png renderer given, doing noting (" + options.renderer + ")");
			}

			break;

		default:
			debug("Sorry! Exporting as '" + type + "' is not supported!")
	}
}
