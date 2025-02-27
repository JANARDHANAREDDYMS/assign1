var checkout = {};

$(document).ready(function() {
  var $messages = $('.messages-content'),
    d, h, m,
    i = 0;

  $(window).on('load', function() {
    $messages.mCustomScrollbar();
    insertResponseMessage('Hi there, I\'m your personal Concierge. How can I help?');
  });

  function updateScrollbar() {
    $messages.mCustomScrollbar("update");
    $messages.mCustomScrollbar("scrollTo", "bottom", {
      scrollInertia: 10,
      timeout: 0
    });
  }

  function setDate() {
    d = new Date();
    if (m != d.getMinutes()) {
      m = d.getMinutes();
      $('<div class="timestamp">' + d.getHours() + ':' + (m < 10 ? '0' + m : m) + '</div>').appendTo($('.message:last'));
    }
  }

  function callChatbotApi(message) {
    var apigClient = apigClientFactory.newClient();
    return apigClient.diningbotPost({}, {
        messages: [{
            type: 'unstructured',
            unstructured: {
                text: message
            }
        }]
    }, {});
}

  function insertMessage() {
    let msg = $('.message-input').val().trim();
    if (msg === '') {
      return false;
    }

    $('<div class="message message-personal">' + msg + '</div>').appendTo($('.mCSB_container')).addClass('new');
    setDate();
    $('.message-input').val(null);
    updateScrollbar();

    callChatbotApi(msg)
      .then((response) => {
        console.log("API Response:", response);

        var data = response.data;
        var body = JSON.parse(data.body); 

        if (body.response && body.response.length > 0) {
          console.log('Received ' + body.response.length + ' messages');

          body.response.forEach((message) => {
            if (message.type === 'unstructured') {
              let html = `
                <div class="message-content">
                  <b>${message.unstructured.text}</b>
                </div>`;
              insertResponseMessage(html);
            } else if (message.type === 'structured' && message.structured.type === 'product') {
              let html = `
                <img src="${message.structured.payload.imageUrl}" width="200" height="240" class="thumbnail" />
                <b>${message.structured.payload.name}<br>$${message.structured.payload.price}</b><br>
                <a href="#" onclick="${message.structured.payload.clickAction}()">
                  ${message.structured.payload.buttonLabel}
                </a>`;
              insertResponseMessage(html);
            } 
            else if (typeof message === 'string') {  // Handling generic text responses
              insertResponseMessage(message);}
            else {
              console.log('Not implemented:', message);
            }
          });
        } else {
          insertResponseMessage('Oops, something went wrong. Please try again.');
        }
      })
      .catch((error) => {
        console.log('An error occurred:', error);
        insertResponseMessage('Oops, something went wrong. Please try again.');
      });
  }

  $('.message-submit').click(function() {
    insertMessage();
  });

  $(window).on('keydown', function(e) {
    if (e.which == 13) {
      insertMessage();
      return false;
    }
  });

  function insertResponseMessage(content) {
    $('<div class="message loading new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure><span></span></div>').appendTo($('.mCSB_container'));
    updateScrollbar();

    setTimeout(function() {
      $('.message.loading').remove();
      $('<div class="message new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>' + content + '</div>').appendTo($('.mCSB_container')).addClass('new');
      setDate();
      updateScrollbar();
      i++;
    }, 500);
  }
});