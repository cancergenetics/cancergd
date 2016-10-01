(function() {
  var out$ = typeof exports != 'undefined' && exports || typeof define != 'undefined' && {} || this;

  var doctype = '<?xml version="1.0" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">';

  function isElement(obj) {
    return obj instanceof HTMLElement || obj instanceof SVGElement;
  }

  function requireDomNode(el) {
    if (!isElement(el)) {
      throw new Error('an HTMLElement or SVGElement is required; got ' + el);
    }
  }

  function isExternal(url) {
    return url && url.lastIndexOf('http',0) == 0 && url.lastIndexOf(window.location.host) == -1;
  }

  function inlineImages(el, callback) {
    requireDomNode(el);

    var images = el.querySelectorAll('image'),
        left = images.length,
        checkDone = function() {
          if (left === 0) {
            callback();
          }
        };

    checkDone();
    for (var i = 0; i < images.length; i++) {
      (function(image) {
        var href = image.getAttributeNS("http://www.w3.org/1999/xlink", "href");
        if (href) {
          if (isExternal(href.value)) {
            console.warn("Cannot render embedded images linking to external hosts: "+href.value);
            return;
          }
        }
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        var img = new Image();  // img.setAttribute('crossOrigin', 'anonymous'); SJB from: http://stackoverflow.com/questions/20424279/canvas-todataurl-securityerror
		// or this problem in IE 11: https://connect.microsoft.com/IE/feedback/details/1013555/ie-11-wrongly-throws-securityerror-on-canvas-todataurl-image-png
		// and: https://developer.microsoft.com/en-us/microsoft-edge/platform/issues/110935/
        href = href || image.getAttribute('href');
        if (href) {
          img.src = href;
          img.onload = function() {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            image.setAttributeNS("http://www.w3.org/1999/xlink", "href", canvas.toDataURL('image/png'));
            left--;
            checkDone();
          }
          img.onerror = function() {
            console.log("Could not load "+href);
            left--;
            checkDone();
          }
        } else {
          left--;
          checkDone();
        }
      })(images[i]);
    }
  }

  function styles(el, selectorRemap) {
    var css = "";
    var sheets = document.styleSheets;
    for (var i = 0; i < sheets.length; i++) {
      try {
        var rules = sheets[i].cssRules;
      } catch (e) {
        console.warn("Stylesheet could not be loaded: "+sheets[i].href);
        continue;
      }

      if (rules != null) {
        for (var j = 0; j < rules.length; j++) {
          var rule = rules[j];
          if (typeof(rule.style) != "undefined") {
            var match, selectorText;

            try {
              selectorText = rule.selectorText;
            } catch(err) {
              console.warn('The following CSS rule has an invalid selector: "' + rule + '"', err);
            }

            try {
              if (selectorText) {
                match = el.querySelector(selectorText);
              }
            } catch(err) {
              console.warn('Invalid CSS selector "' + selectorText + '"', err);
            }

            if (match) {
              var selector = selectorRemap ? selectorRemap(rule.selectorText) : rule.selectorText;
              css += selector + " { " + rule.style.cssText + " }\n";
            } else if(rule.cssText.match(/^@font-face/)) {
              css += rule.cssText + '\n';
            }
          }
        }
      }
    }
    return css;
  }

  function getDimension(el, clone, dim) {
    var v = (el.viewBox && el.viewBox.baseVal && el.viewBox.baseVal[dim]) ||
      (clone.getAttribute(dim) !== null && !clone.getAttribute(dim).match(/%$/) && parseInt(clone.getAttribute(dim))) ||
      el.getBoundingClientRect()[dim] ||
      parseInt(clone.style[dim]) ||
      parseInt(window.getComputedStyle(el).getPropertyValue(dim));
    return (typeof v === 'undefined' || v === null || isNaN(parseFloat(v))) ? 0 : v;
  }

  function reEncode(data) {
    data = encodeURIComponent(data);
    data = data.replace(/%([0-9A-F]{2})/g, function(match, p1) {
      var c = String.fromCharCode('0x'+p1);
      return c === '%' ? '%25' : c;
    });
    return decodeURIComponent(data);
  }

  out$.svgAsDataUri = function(el, options, cb) {
    requireDomNode(el);

    options = options || {};
    options.scale = options.scale || 1;
    var xmlns = "http://www.w3.org/2000/xmlns/";

    inlineImages(el, function() {
      var outer = document.createElement("div");
      var clone = el.cloneNode(true);
      var width, height;
      if(el.tagName == 'svg') {
        width = options.width || getDimension(el, clone, 'width');
        height = options.height || getDimension(el, clone, 'height');
      } else if(el.getBBox) {
        var box = el.getBBox();
        width = box.x + box.width;
        height = box.y + box.height;
        clone.setAttribute('transform', clone.getAttribute('transform').replace(/translate\(.*?\)/, ''));

        var svg = document.createElementNS('http://www.w3.org/2000/svg','svg')
        svg.appendChild(clone)
        clone = svg;
      } else {
        console.error('Attempted to render non-SVG element', el);
        return;
      }

      clone.setAttribute("version", "1.1");
      if (!clone.getAttribute('xmlns')) {
        clone.setAttributeNS(xmlns, "xmlns", "http://www.w3.org/2000/svg");
      }
      if (!clone.getAttribute('xmlns:xlink')) {
        clone.setAttributeNS(xmlns, "xmlns:xlink", "http://www.w3.org/1999/xlink");
      }
      clone.setAttribute("width", width * options.scale);
      clone.setAttribute("height", height * options.scale);
      clone.setAttribute("viewBox", [
        options.left || 0,
        options.top || 0,
        width,
        height
      ].join(" "));

      var fos = clone.querySelectorAll('foreignObject > *');
      for (var i = 0; i < fos.length; i++) {
        fos[i].setAttributeNS(xmlns, "xmlns", "http://www.w3.org/1999/xhtml");
      }

      outer.appendChild(clone);

      var css = styles(el, options.selectorRemap);
      var s = document.createElement('style');
      s.setAttribute('type', 'text/css');
      s.innerHTML = "<![CDATA[\n" + css + "\n]]>";
      var defs = document.createElement('defs');
      defs.appendChild(s);
      clone.insertBefore(defs, clone.firstChild);

      var svg = doctype + outer.innerHTML;
      var uri = 'data:image/svg+xml;base64,' + window.btoa(reEncode(svg));
      if (cb) {
        cb(uri);
      }
    });
  }

  out$.svgAsPngUri = function(el, options, cb) {
    requireDomNode(el);

    out$.svgAsDataUri(el, options, function(uri) {
      var image = new Image();
	  image.setAttribute('crossOrigin', 'anonymous'); // added by SJB to try to fix IE 11 issue.
      image.onload = function() {
        var canvas = document.createElement('canvas');
        canvas.width = image.width;
        canvas.height = image.height;
        var context = canvas.getContext('2d');
        if(options && options.backgroundColor){
          context.fillStyle = options.backgroundColor;
          context.fillRect(0, 0, canvas.width, canvas.height);
        }
        try {		
          context.drawImage(image, 0, 0);
		// Throws error in IE 11 (and other IEs): http://stackoverflow.com/questions/24346090/drawimage-raises-script65535-on-ie11
// and: https://connect.microsoft.com/IE/feedback/details/809823/draw-svg-image-on-canvas-context		
        }
        catch (err) {
		   // So will try again:
           setTimeout(function() {context.drawImage(image, 0, 0)}, 1);  // setTimeout(function() {drawPiece(ctx,x,y,type,color)}, 1);
		   alert("Error: Internet explorer has issues converting SVG to PNG images. Try using another webbrowser, such as Firefox, Opera, Chrome or Safari")
        }
/* Will see if the IE update fixes this: https://www.microsoft.com/en-us/download/details.aspx?id=51031 */		
/* A fix given was:
image.onload = function() {
  try {
    ctx.drawImage(image,x,y,40,40);
  }
  catch (err)
  {
    setTimeout(function() {drawPiece(ctx,x,y,type,color)}, 1);
  }
};
*/		
        var a = document.createElement('a'), png;
        try {
          png = canvas.toDataURL('image/png');
        } catch (e) {
          if ((typeof SecurityError !== 'undefined' && e instanceof SecurityError) || e.name == "SecurityError") {
            console.error("Rendered SVG images cannot be downloaded in this browser.");
			alert('Rendered SVG to PNG images cannot be downloaded using this button in this browser, due to an issue with the browser\'s "canvas.toDataURL()" function.\n\nInstead if you are using Internet Explorer: with mouse pointer on the boxplot image, click the RIGHT mouse button, then from the popup menu choose "Save picture as...", then in the save dialog that appears, for the "Save as type" choose "PNG (*.png)", then "Save". If that doesn\'t work, then then try Firefox, Opera, Chrome or Safari browsers.');
            return;
          } else {
            throw e;
          }
        }
        cb(png);
      }
      image.onerror = function(error) {
        console.error('There was an error loading the data URI as an image', error);
      }
      image.src = uri;
    });
  }

  function download(name, uri) {
    var a = document.createElement('a');
    a.download = name;
    a.href = uri;
    document.body.appendChild(a);
    a.addEventListener("click", function(e) {
      a.parentNode.removeChild(a);
    });
    a.click();
  }

  out$.saveSvg = function(el, name, options) {
    requireDomNode(el);

    options = options || {};
    out$.svgAsDataUri(el, options, function(uri) {
      download(name, uri);
    });
  }

  out$.saveSvgAsPng = function(el, name, options) {
    requireDomNode(el);

    options = options || {};
    out$.svgAsPngUri(el, options, function(uri) {
      download(name, uri);
    });
  }

  // if define is defined create as an AMD module
  if (typeof define !== 'undefined') {
    define(function() {
      return out$;
    });
  }
})();
