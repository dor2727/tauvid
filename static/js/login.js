function setCookie(name, value) {
    document.cookie = name + "=" + (value || "") + "; path=/";
}

function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function toggle_login() {
    var sheet = document.getElementById('gapi-style');
    sheet.innerText = `
        .auth {
            display: initial;
        }

        .unauth {
            display: none;
        }
    `;
}

function setErrorText(text) {
    document.getElementById('login-error').innerHTML = text;
}

function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();
    console.log("ID: " + profile.getId()); // Don't send this directly to your server!
    console.log("Email: " + profile.getEmail());

    // The ID token you need to pass to your backend:
    var id_token = googleUser.getAuthResponse().id_token;
    console.log("ID Token: " + id_token);
    validate_account(googleUser);

}

function onFailure(error) {
  console.log(error);
  setErrorText(error);
}

function is_tau_domain(domain) {
    return domain && typeof(domain) == "string" && domain.endsWith("tau.ac.il");
}

function validate_account(user) {
    var signed_in = user.isSignedIn();
    var domain = user.getHostedDomain();
    console.log(signed_in, domain, is_tau_domain(domain), user.getAuthResponse().id_token);

    if(signed_in && !is_tau_domain(domain)) {
        sign_out(gapi.auth2.getAuthInstance())();
        setErrorText("Sign in with a TAU email");
    }

    else if(signed_in && is_tau_domain(domain)) {
        toggle_login();
        setCookie("LOGIN", user.getAuthResponse().id_token + "!" + user.getBasicProfile().getEmail() + ";secure;samesite=strict");
    }
}


function sign_out(authInstance) {
    return function() {
        setCookie("LOGIN", "");
        authInstance.signOut().then(function() {
          window.location.href = '/';
        });
    };
}


function init_gapi() {
    gapi.load('auth2', function() {
        gapi.auth2.init({
            client_id: '55911848801-gf0dm7722gu9pqtj57990n2lvq12vcv8.apps.googleusercontent.com',
            scope: 'email',
            fetch_basic_profile: false
        }).then(function (authInstance) {
            var sign_in_btn = document.getElementById('sign-in');
            authInstance.attachClickHandler(sign_in_btn, {}, onSignIn, onFailure);

            var sign_out_btn = document.getElementById('sign-out');
            sign_out_btn.addEventListener('click', sign_out(authInstance));

            var user = authInstance.currentUser.get();
            validate_account(user);

        });
    });
}

function signed_in() {
    cookie = getCookie("LOGIN");
    if(cookie) {
        return cookie.includes('tau.ac.il');
    }
    return false;
}

function onReady(callback){
    if (document.readyState!='loading') {
        callback();
    } else {
        document.addEventListener('DOMContentLoaded', callback);
    }
}


onReady(function() {
    if(signed_in()) {
        toggle_login();
    }
});
