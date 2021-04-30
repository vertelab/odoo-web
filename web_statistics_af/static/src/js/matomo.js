// console.log("Matomo script commencing...");
// console.log("0a");
odoo.define('web_statistics_af.matomo_tag_src', function(require) {
    "use strict";
    var rpc = require('web.rpc');

    var _mtm = _mtm || [];
    if (_mtm) {
      // console.log("Matomo declared.");

      const entry1 = {
        "mtm.startTime": new Date().getTime(),
        "event": "mtm.Start"
      };

      const entry2 = {
        "mtm.startTime": new Date().getTime(),
        "timestamp": new Date(),
        "event": "crm_test"
      };

      // _mtm.push(entry1);
      // _mtm.push(entry2);
      console.log("Matomo script completed.", entry1, entry2);
    } else {
      console.error("Matomo global object not found.");
    }

     var matomo_data = matomo_data || [];
     const matomo_entry = {
       "mtm.startTime": new Date().getTime(),
       "event": "mtm.Start"
     };
     matomo_data.push(matomo_entry);

     const html = document;
     const matomo_tag = html.createElement("script");
     const script_tag = html.getElementsByTagName("script")[0];

     matomo_tag.type = "text/javascript";
     matomo_tag.async = true;
     matomo_tag.defer = true;

     var get_matomo_url = rpc.query({
            model: 'ir.config_parameter',
            method: 'get_param',
            args: ['web_statistics_af.matomo_tag_src'],
        })
        .then(function (result) {
            console.log("result =-=-=", result);
            matomo_tag.src = result;
            console.log("Matomo tag Source =-=-", matomo_tag.src);
            script_tag.parentNode.insertBefore(matomo_tag, script_tag);
        }, function(){
            return False;
            }
        );
     // matomo_tag.src = "https://af-staging.analytics.elx.cloud/js/container_ew8X7e8B.js";
     // matomo_tag.src = "http://af-staging.analytics.elx.cloud/js/container_ew8X7e8B.js";
     // matomo_tag.src = "af-staging.analytics.elx.cloud/js/container_ew8X7e8B.js";
     // matomo_tag.src = "//af-staging.analytics.elx.cloud/js/container_ew8X7e8B.js";
//     matomo_tag.src = "https://af.analytics.elx.cloud/js/container_4v00kfpD.js";


//     console.log("Matomo script completed.", matomo_tag);
//     script_tag.parentNode.insertBefore(matomo_tag, script_tag);

//     console.log("Matomo script completed.", matomo_data);

});
