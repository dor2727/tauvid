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
}

function is_tau_domain(domain) {
    return domain && typeof(domain) == "string" && domain.endsWith("tau.ac.il");
}

function validate_account(user) {
    var signed_in = user.isSignedIn();
    var domain = user.getHostedDomain();
    console.log(signed_in, domain, is_tau_domain(domain));

    if(!signed_in) {
        // window.location.href = '/';
    }

    if(signed_in && !is_tau_domain(domain)) {
        sign_out(gapi.auth2.getAuthInstance())();
    }
}


function sign_out(authInstance) {
    return function() {
        authInstance.signOut().then(function() {
          window.location.href = '/';
        });
    };
}


function attachSignin(element) {
    console.log(element.id);
    
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