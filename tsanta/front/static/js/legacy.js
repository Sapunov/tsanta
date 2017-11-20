function validateEmail(email) {
  var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(email);
}

function changeUni(form) {
  var serializedForm = serializeForm(form),
    resultsBox = ge("se-results"),
    out = "",
    str = [];

  if (f.vuz.trim() == "") {
    return form.vuz.focus(), !1;
  }

  if (f.vuz.length >= 2) {
    $.post("ajax.php", {
      "act": "search",
      "text": f.vuz
    }, function(data, status) {
      if (status == "success") {
        console.log(data);
        str = parseJSON(data);
        if (str.length > 0) {
          out += "<h3>Уточним ВУЗ:</h3>";
          each(str, function(i, e) {
            out += "<a class='search-results' href='" + e.way + "'>" + e.ans + "</a>"
          });
        } else {
          out = "Ой ой ой!<br>Тайный Санта доберется до Вас уже в следующем году";
        }

        resBox.style.display = "block";
        resBox.innerHTML = out;
        return !1;
      }
    });
  }
  return !1;
}

function recipient(form) {
  var f = serializeForm(form),
    resBox = ge("se-results"),
    out = "";
  if (f.email.trim() == "") {
    return form.email.focus(), !1;
  }
  if (validateEmail(f.email)) {
    $.post("ajax.php", {
      "act": "recipient",
      "email": f.email
    }, function(data, status) {
      if (status == "success") {
        console.log(data);
        out = parseJSON(data);
        console.log(out);

        document.write(out);
        return !1;
      }
    });
  } else {
    return form.email.focus(), !1;
  }
  return !1;
}

function santa(form) {
  var f = serializeForm(form),
    resBox = ge("se-results"),
    out = "";
  if (f.email.trim() == "") {
    return form.email.focus(), !1;
  }
  if (validateEmail(f.email)) {
    $.post("ajax.php", {
      "act": "santa",
      "email": f.email
    }, function(data, status) {
      if (status == "success") {
        out = parseJSON(data);

        if (out == "not") {
          resBox.style.display = "block";
          resBox.innerHTML = "<h2 style='text-align:center;'>Ошибочка! Не можем найти Вашего Санту.</h2>";
        } else if (out) {
          resBox.style.display = "block";
          var html = "";
          for(var i = 0; i < out.length; i ++) {
            html += '<p><b><a href="' + out[i].vk + '" target="blank">' + out[i].name + '</a></b></p>';
          }
          resBox.innerHTML = "<h2 style='text-align:center;'>Ваш Тайный Санта:</h2>" + html;
        }
        console.log(out);

        return !1;
      }
    });
  } else {
    return form.email.focus(), !1;
  }
  return !1;
}

var use_ajax = false;

function saveForm(form) {
  var f = serializeForm(form),
    imp = [
      form.name,
      form.surname,
      form.sex,
      form.email,
      form.phone,
      form.vk,
      form.interests,
      form.inpresent,
      form.present
    ],
    ans = 0;

  for (var i = 0; i <= imp.length - 1; i++) {
    if (imp[i].value == 0 || imp[i] == "") {
      return imp[i].focus(), !1;
    }
  }
  if (!validateEmail(form.email.value)) {
    return form.email.focus(), !1;
  }

  if (!use_ajax) {
    use_ajax = true;
    form.but.innerHTML = "Загрузка...";
    $.post("ajax.php", f, function(data, status) {
      if (status == "success") {
        console.log(data);
        use_ajax = false;
        ans = parseJSON(data);
        if (ans == 200) {
          document.location.href = 'thanks';
        } else {
          ajax.error("Ошибка загрузки содержимого.");
        }
        return !1;
      }
    });
  }
  return !1;
}
