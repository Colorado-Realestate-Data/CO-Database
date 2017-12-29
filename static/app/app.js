/****************************************
 **************** Mixins ****************
 ****************************************/
String.prototype.format = String.prototype.f = function() {
    var s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};
const UtilMixin = {
methods: {
    formatDate: function (value, fmt, _default) {
        _default = (_default === undefined? '': _default);
        if (!value) {
            return _default;
        }
        fmt = (fmt === undefined)? 'MMM D, YYYY HH:mm' : fmt;
        return moment(value).format(fmt);
    },
    formatBoolean: function (value) {
        return '<span class="fa fa-{0}"></span>'.f(value? 'check text-success': 'close text-danger');
    },
    ifEmptyFormat: function (value, _default) {
        return value || (_default || '-');
    },
    formatPath: function (path) {
        return (path || '').split('\\').pop().split('/').pop();
    },
    formatFileSize: function (value, _default) {
        _default = (_default === undefined? '': _default);
        const UNITS = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        if (value === null || value === undefined) {
            return _default;
        }
        if (!Number.isFinite(value)) {
            throw new TypeError('Expected a finite number');
        }
        const neg = value < 0;
        if (neg) {
            value = -value;
        }
        if (value < 1) {
            return (neg ? '-' : '') + value + ' B';
        }
        const exponent = Math.min(Math.floor(Math.log10(value) / 3), UNITS.length - 1);
        const valueStr = Number((value / Math.pow(1000, exponent)).toPrecision(3));
        const unit = UNITS[exponent];
        return (neg ? '-' : '') + valueStr + ' ' + unit;
    },
    getCookie: function (cName) {
        if (document.cookie.length > 0) {
            cStart = document.cookie.indexOf(cName + "=");
            if (cStart !== -1) {
                cStart = cStart + cName.length + 1;
                cEnd = document.cookie.indexOf(";", cStart);
                if (cEnd === -1) cEnd = document.cookie.length;
                return encodeURI(document.cookie.substring(cStart, cEnd));
            }
        }
        return "";
    },
    showMessage: function(msg, type, delay) {
        $.bootstrapGrowl(msg, {
          ele: 'body', // which element to append to
          type: type || 'info', // (null, 'info', 'danger', 'success')
          offset: {from: 'top', amount: 20}, // 'top', or 'bottom'
          align: 'center', // ('left', 'right', or 'center')
          width: 'auto', // (integer, or 'auto')
          delay: delay !== undefined? delay: 5000, // Time while the message will be displayed. It's not equivalent to the *demo* timeOut!
          allow_dismiss: true, // If true then will display a cross to close the popup.
          stackup_spacing: 10 // spacing between consecutively stacked growls.
        });
    },
    showSuccess: function(msg, delay) {
        this.showMessage(msg, 'success', delay)
    },
    showError: function(msg, delay) {
        this.showMessage(msg, 'danger', delay)
    },
    showWarn: function(msg, delay) {
        this.showMessage(msg, 'warning', delay)
    },
    showDefaultServerSuccess: function(response, delay) {
        delay = delay !== undefined? delay: 5000;
        defaultMsg = 'Operation done successfully';
        this.showSuccess(response.statusText || defaultMsg, delay);
    },
    showDefaultServerError: function(error, showReason, delay, extra_message) {
        response = error.response || error.request;
        var msg;
        delay = delay !== undefined? delay: 5000;
        showReason = showReason !== undefined? showReason: true;
        if (!response || response.status <= 0) {
            msg = "<strong>Server Connection Error</strong>";
        } else if(response.status === 401) {
            msg = "<strong>Session is expired.</strong> <br>You are redirecting to login page ...";
            var next = window.location.pathname+window.location.hash;
            setTimeout(function() {
                window.location = '/?next=' + next;
            }, 2000)
        } else {
            msg = "<strong>"+response.status + ": " + response.statusText + "</strong>";
            var jData = this.safeFromJson(response.data);
            if (showReason && jData) {
                msg += '<p>'+ this.prettifyError(response.data) + '</p>';
            }
            if (extra_message) {
                msg += '<p>'+extra_message+'</p>';
            }
        }
        this.showError(msg, delay);
    },
    prettifyError: function(data) {
        return JSON.stringify(data).replace(",", "<br>").replace(/\[|\]|\}|\{/g, "");
    },
    safeFromJson: function(s, nullIfFail) {
        if (typeof s === 'object') {
            return s;
        }
        nullIfFail = nullIfFail === undefined;
        try {
            return angular.fromJson(s);
        } catch(e) {
            return nullIfFail? null: s;
        }
    },
    randomId: function(n) {
        n = n || 10;
        return Math.floor((Math.random() * Math.pow(10, n)) + 1);
    },
    addQSParm: function(url, name, value) {
        var re = new RegExp("([?&]" + name + "=)[^&]+", "");

        function add(sep) {
            url += sep + name + "=" + encodeURIComponent(value);
        }

        function change() {
            url = url.replace(re, "$1" + encodeURIComponent(value));
        }
        if (url.indexOf("?") === -1) {
            add("?");
        } else {
            if (re.test(url)) {
                change();
            } else {
                add("&");
            }
        }
        return url;
    },
    noCacheUrl: function(url) {
        var r = this.randomId();
        return this.addQSParm(url, 'nc', r);
    },
    download: function downloadURL(url) {
        var hiddenIFrameID = 'hiddenDownloader',
            iframe = document.getElementById(hiddenIFrameID);
        if (iframe === null) {
            iframe = document.createElement('iframe');
            iframe.id = hiddenIFrameID;
            iframe.style.display = 'none';
            document.body.appendChild(iframe);
        }
        iframe.src = url;
    }
}
};

const UiMixin = {
    methods: {
        modifyStatusFormat: function (value) {
            var statusMap = {
                created: ['Created', 'success'],
                modified: ['Modified', 'primary'],
                deleted: ['Deleted', 'danger'],
                moved: ['Moved', 'warning'],
                no_change: ['No Change', 'default']
            }, c = statusMap[value] || [value, 'default'];

            return '<span class="text text-{0}">{1}</span>'.f(c[1], c[0]);
        },
        validityStatusFormat: function (value) {
            var statusMap = {
                valid: ['Valid', 'success', 'fa fa-check'],
                protected: ['Protected', 'primary', 'fa fa-lock'],
                invalid: ['Invalid', 'danger', 'fa fa-warning'],
                unknown: ['Unknown', 'warning', 'fa fa-question'],
                not_support: ['Unsupport', 'default', 'fa fa-close'],
                not_checked: ['N/A', 'default', '']
            }, c = statusMap[value] || [value, 'default'];
            return '<span class="text text-{0}"><span class="{1}"></span> {2}</span>'.f(c[1], c[2], c[0]);
        }
    }
};

const VuetablePaginationBootstrap = Vue.component('vuetable-pagination-bootstrap', {
    template: '#vuetable-pagination-bootstrap-template',
    mixins: [Vuetable.VuetablePaginationMixin]
});

const VuetableBootstrapMixin = {
    data: function() {
        return {
            loadingOverlay: false,
            tablePerPage: 10,
            tableFiltering: {},
            pageSizeOptions: [10, 25, 50, 100, 200, 0],
            tableHTTPOptions: {
                paramsSerializer: function(params) {
                    var newParams = {};
                    for (var k in params) {
                        newParams[k] = params[k] === null? undefined:params[k];
                    }
                    return axios.defaults.paramsSerializer(newParams);
                }
            },
            css: {
                table: {
                    tableClass: 'table table-striped table-hover table-advance sortable',
                    loadingClass: 'loading',
                    ascendingIcon: 'fa fa-sort-asc',
                    descendingIcon: 'fa fa-sort-desc',
                    handleIcon: 'glyphicon glyphicon-menu-hamburger'
                }
            }
        }
    },
    watch: {
        tablePerPage: function (val, oldVal) {
            this.$nextTick(function () {
                this.$refs.vuetable.refresh();
            })
        },
        tableFiltering: {
            handler: function (val, oldVal) {
                this.$nextTick(function () {
                    this.$refs.vuetable.refresh();
                })
            },
            deep: true
        }
    },
    components: {
        'vuetable': Vuetable.Vuetable,
        'vuetable-pagination': VuetablePaginationBootstrap,
        'vuetable-pagination-info': Vuetable.VuetablePaginationInfo
    },
    methods: {
        getSortParam: function (sortOrder) {
            return sortOrder.map(function (sort) {
                return (sort.direction === 'desc' ? '' : '-') + (sort.sortField || sort.field)
            }).join(',');
        },
        onPaginationData: function (paginationData) {
            paginationData.from = (paginationData.current_page -1) * paginationData.page_size + 1;
            paginationData.to = Math.min(paginationData.current_page * paginationData.page_size, paginationData.total);
            this.$refs.pagination.setPaginationData(paginationData);
            this.$refs.paginationInfo.setPaginationData(paginationData);
        },
        onChangePage: function (page) {
            this.$refs.vuetable.changePage(page);
        },
        OnLoadErrorData: function (response) {
            this.showDefaultServerError(response);
        },
        OnLoadedData: function (page) {
            this.loadingOverlay = false;
        },
        OnLoadingData: function (page) {
            this.loadingOverlay = true;
        }
    }
};

const LoadingOverlayableMixin = {
    data: function () {
        return {
            loadingOverlay: false
        }
    }
};

/****************************************
 *********** Util Components ************
 ****************************************/
Vue.component('confirm', {
    template: '#confirm-template',
    props: {
        btnClass: String,
        sureClass: String,
        yesClass: String,
        noClass: String,
        confirmingIconClass: String,
        confirming: {
            type: Boolean,
            default: false
        },
        'func': {
            type: Function,
            required: true
        },
        yesText: {
            type: String,
            default: 'Yes'
        },
        noText: {
            type: String,
            default: 'No'
        },
        sureText: {
            type: String,
            default: 'Sure?'
        },
        confirmingText: {
            type: String,
            default: ''
        }
    },
    data: function() {
        return {
            confirm: false
        };
    }
});

Vue.component('select2', {
    template: '<select><slot></slot></select>',
    props: ['options', 'value', 'initParams'],
    mounted: function () {
        var vm = this;
        $(this.$el).select2(Object.assign({}, {data: this.options}, this.initParams))
        .val(this.value).trigger('change').on('change', function () {
            var value = $(this).val();
            if (JSON.stringify(vm.value) !== JSON.stringify(value)) {
                vm.$emit('input', value);
            }
        })
        // to prevent open dropdown after un-select items
        .on('select2:unselecting', function(e) {
            $(this).data('unselecting', true);
        })
        .on('select2:open', function(e) {
            var $el = $(this);
            if ($el.data('unselecting')) {
                $el.removeData('unselecting');
                $el.select2('close');
            }
        });
    },
    watch: {
        value: function (value, oldValue) {
            if (JSON.stringify(value) !== JSON.stringify(oldValue)) {
                $(this.$el).val(value).trigger("change");
            }
        },
        options: function (options) {
            // update options
            $(this.$el).select2(Object.assign({}, {data: options}, this.initParams)).trigger('change');
        }
    },
    destroyed: function () {
        $(this.$el).off().select2('destroy');
    }
});

Vue.component('vue-datetimepicker', {
    template: '<div class="input-group date">' +
                '<input type="text" class="form-control" :placeholder="inputPlaceholder" />' +
                '<span class="input-group-addon">' +
                  '<span class="glyphicon glyphicon-calendar"></span>' +
                '</span>' +
              '</div>',
    props: ['options', 'value', 'inputPlaceholder'],
    model: {
        prop: 'value',
        event: 'change'
    },
    watch: {
        options: function (options) {
            $(this.$el).datetimepicker({data: options})
        },
        value: function (value, oldValue) {
            if (JSON.stringify(value || null) !== JSON.stringify(oldValue || null)) {
                $(this.$el).data("DateTimePicker").date(value);
            }
        }
    },
    mounted: function () {
        var vm = this;
        $(this.$el).datetimepicker(this.options).on('dp.change', function (e) {
            var value = e.date?e.date.toDate():'';
            if (JSON.stringify(vm.value || null) !== JSON.stringify(value || null)) {
                vm.value = value;
                vm.$emit('change', vm.value);
            }
        })
    },
    destroyed: function () {
        $(this.$el).off().datetimepicker('destroy')
    }
});

/****************************************
 ************ App Components ************
 ****************************************/
/* CONSTANTS */

Vue.component('main-header', {
    template: '#mainheader-template',
    mixins: [UtilMixin],
    methods: {
        logout: function () {
            var self = this;
            this.$http.delete('session').then(function () {
                window.location = '/?next=' + window.location.pathname;
            }, function (error) {
                self.showDefaultServerError(error)
            })
        }
    }
});

Vue.component('side-menu', {
    template: '#sidemenu-template',
    methods: {
        isActive: function () {
            return Array.from(arguments).indexOf(this.$route.name)>=0
        }
    }
});

Vue.component('page-bar', {
    template: '#pagebar-template'
});

const MyProfile = Vue.component('my-profile', {
    template: '#myprofile-template',
    mixins: [UtilMixin, LoadingOverlayableMixin],
    data: function () {
        return {
            profileChosenFile: null,
            uploadingAvatar: false,
            deletingAvatar: false,
            savingPersonalInfo: false,
            changingPassword: false,
            userPassword: {
                current_password: '',
                new_password: '',
                re_new_password: ''
            },
            userProfile: {
                email: null,
                first_name: null,
                last_name: null,
                profile: {
                    gender: null
                }
            }
        }
    },
    created: function() {
        var self = this;
        this.$http.get('me').then(function (response) {
            var user = response.data;
            store.state.currentUser = user;
            self.userProfile.email = user.email;
            self.userProfile.first_name = user.first_name;
            self.userProfile.last_name = user.last_name;
            self.userProfile.profile.gender = user.profile.gender;
        }, function (error) {
            self.showDefaultServerError(error)
        });
    },
    computed: {
        passwordMatched: function () {
            return this.userPassword.new_password === this.userPassword.re_new_password;
        }
    },
    methods: {
        deleteAvatar: function() {
            var self = this;
            this.deletingAvatar = true;
            this.$http.delete('me/avatar').then(function (response) {
                var res = response.data;
                store.state.currentUser.profile.avatar = res.avatar;
                self.deletingAvatar = false;
                self.showSuccess('Avatar deleted successfully', 5000);
            }, function (error) {
                self.deletingAvatar = false;
                self.showDefaultServerError(error);
            });
        },
        clearChosenAvatar: function () {
            this.profileChosenFile = null;
            $('#profile_image').val('');
        },
        onChangeProfileFile: function (event) {
            if (event.target.files.length > 0) {
                this.profileChosenFile = event.target.files[0];
            }
        },
        updateAvatar: function () {
            if (!this.profileChosenFile) return;
            var f = this.profileChosenFile,
                fileName = f.name,
                r = new FileReader(),
                self = this;
            r.onloadend = function (e) {
                var data = e.target.result;
                self.$http.put('me/avatar', data, {
                    headers: {
                        'Content-Type': 'application/base64',
                        'Content-Disposition': 'attachment; filename='+fileName
                    }
                }).then(function (response) {
                    var res = response.data;
                    self.clearChosenAvatar();
                    store.state.currentUser.profile.avatar = res.avatar;
                    self.uploadingAvatar = false;
                    self.showSuccess('Avatar uploaded successfully', 5000);
                }, function (error) {
                    self.uploadingAvatar = false;
                    self.showDefaultServerError(error);
                });
            };
            this.uploadingAvatar = true;
            r.readAsDataURL(f);
        },
        saveProfileInfo: function () {
            var self = this;
            this.savingPersonalInfo = true;
            this.$http.put('me', this.userProfile).then(function(response) {
                user = response.data;
                store.state.currentUser = response.data;
                self.savingPersonalInfo = false;
                self.showSuccess('Profile updated successfully', 5000);
            }, function(error) {
                self.savingPersonalInfo = false;
                self.showDefaultServerError(error);
            });
        },
        changePassword: function () {
            var self = this;
            this.changingPassword = true;
            this.$http.post('me/password', this.userPassword).then(function(response) {
                self.userPassword = {};
                self.changingPassword = false;
                self.showSuccess('Password changed successfully', 5000);
            }, function(response) {
                self.changingPassword = false;
                self.showDefaultServerError(response, true);
            });
        }
    }
});

const Dashboard = Vue.component('dashboard', {
    template: '#dashboard-template',
    mixins: [LoadingOverlayableMixin],
    mounted: function () {
        Index.initCharts();
    }
});

const ExcludePatterns = Vue.component('exclude-patterns', {
    template: '#excludepattern-list-template',
    mixins: [UtilMixin, VuetableBootstrapMixin],
    data: function () {
        return {
            tableUrl: '/api/v1/exclude_pattern/',
            tablePerPage: 0,
            tableFiltering: {
                pattern: null
            },
            tableFields: [
                {name: 'id', sortField: 'id', title: 'ID#', callback: 'idFormat'},
                {name: 'pattern', sortField: 'pattern', title: 'Pattern', callback: 'patternFormat'},
                {name: 'get_history', sortField: 'get_history', title: 'Ignore History?', callback: 'formatBoolean'},
                {name: 'get_scan', sortField: 'get_scan', title: 'Don\'t Scan?', callback: 'formatBoolean'},
                {name: 'get_usage', sortField: 'get_usage', title: 'Ignore Disk Usage?', callback: 'formatBoolean'},
                {name: 'active', sortField: 'active', title: 'Enabled?', callback: 'formatBoolean'},
                '__slot:actions'
            ]
        }
    },
    mounted: function () {
        EventsBus.$on('excludepatterns:table-updated', this.onUpdatedEvent);
    },
    destroyed: function () {
        EventsBus.$off('excludepatterns:table-updated', this.onUpdatedEvent);
    },
    methods: {
        onUpdatedEvent: function () {
            this.$refs.vuetable.refresh();
        },
        idFormat: function (value) {
            return '<span class="text-primary">{0}</span>'.f(value);
        },
        patternFormat: function (value) {
            return '<span class="text-primary">{0}</span>'.f(value);
        },
        clearFilters: function () {
            this.tableFiltering = {
                pattern: null
            };
        },
        deleteRecord: function (record) {
            var self = this;
            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this record!",
                icon: "warning",
                buttons: {
                    cancel: "Cancel",
                    yes: {
                        text: "Yes, Delete it!",
                        value: true,
                        className: "btn-danger",
                        closeModal: false
                    }
                },
                dangerMode: true
            }).then(function (willDelete) {
                if (willDelete) {
                    self.$http.delete('exclude_pattern/{0}/'.f(record.id)).then(function (response) {
                        swal.stopLoading();
                        swal.close();
                        self.showSuccess('Record deleted successfully', 5000);
                        EventsBus.$emit('excludepatterns:table-updated');
                    }, function (error) {
                        swal.stopLoading();
                        self.showDefaultServerError(error);
                    });
                }
            });
        }
    }
});

const NewExcludePattern = Vue.component('new-exclude-pattern', {
    template: '#excludepattern-form-template',
    mixins: [UtilMixin, LoadingOverlayableMixin],
    data: function () {
        return {
            saving: false,
            record: {
                pattern: null, get_history: true, get_scan: true, get_usage: true, active: true
            }
        }
    },
    methods: {
        saveRecord: function () {
            var self = this;
            self.saving = true;
            this.$http.post('exclude_pattern', this.record).then(function(response) {
                self.saving = false;
                self.showSuccess('Pattern added successfully', 5000);
                self.$router.push({name: 'exclude_patterns'});
                EventsBus.$emit('excludepatterns:table-updated');
            }, function(error) {
                self.saving = false;
                self.showDefaultServerError(error);
            });
        }
    }
});

const EditExcludePattern = Vue.component('edit-exclude-pattern', {
    template: '#excludepattern-form-template',
    mixins: [UtilMixin, LoadingOverlayableMixin],
    data: function () {
        return {
            saving: false,
            record: {}
        }
    },
    created: function() {
        var self = this,
            recordId = this.$route.params.record_id;
        this.loadingOverlay = true;
        this.$http.get('exclude_pattern/{0}/'.f(recordId)).then(function (response) {
            self.loadingOverlay = false;
            self.record = response.data;
        }, function (error) {
            self.loadingOverlay = false;
            self.showDefaultServerError(error)
        });
    },
    methods: {
        saveRecord: function () {
            var self = this,
                recordId = this.$route.params.record_id;
            self.saving = true;
            this.$http.put('exclude_pattern/{0}/'.f(recordId), this.record).then(function(response) {
                self.saving = false;
                self.showSuccess('Pattern updated successfully', 5000);
                self.$router.push({name: 'exclude_patterns'});
                EventsBus.$emit('excludepatterns:table-updated');
            }, function(error) {
                self.saving = false;
                self.showDefaultServerError(error);
            });
        }
    }
});

/* Admin Components */

const AdminUsers = Vue.component('admin-users', {
    template: '#admin-user-list-template',
    mixins: [UtilMixin, VuetableBootstrapMixin],
    data: function () {
        return {
            tableUrl: '/api/v1/admin/user/',
            tablePerPage: 0,
            tableFiltering: {
                pattern: null
            },
            tableFields: [
                {name: 'id', sortField: 'id', title: 'ID#', callback: 'idFormat'},
                {name: '__slot:username', sortField: 'username', title: 'Username', callback: 'usernameFormat'},
                {name: 'email', sortField: 'email', title: 'E-mail', callback: 'ifEmptyFormat'},
                {name: 'first_name', sortField: 'first_name', title: 'First Name', callback: 'ifEmptyFormat'},
                {name: 'last_name', sortField: 'last_name', title: 'Last Name', callback: 'ifEmptyFormat'},
                {name: 'is_superuser', sortField: 'is_superuser', title: 'Superuser?', callback: 'formatBoolean'},
                {name: 'is_staff', sortField: 'is_staff', title: 'Staff?', callback: 'formatBoolean'},
                {name: 'is_active', sortField: 'is_active', title: 'Active?', callback: 'formatBoolean'},
                '__slot:actions'
            ]
        }
    },
    mounted: function () {
        EventsBus.$on('admin-users:table-updated', this.onUpdatedEvent);
    },
    destroyed: function () {
        EventsBus.$off('admin-users:table-updated', this.onUpdatedEvent);
    },
    methods: {
        onUpdatedEvent: function () {
            this.$refs.vuetable.refresh();
        },
        idFormat: function (value) {
            return '<span class="text-primary">{0}</span>'.f(value);
        },
        usernameFormat: function (value) {
            return '<span class="text-primary">{0}</span>'.f(value);
        },
        clearFilters: function () {
            this.tableFiltering = {
                pattern: null
            };
        },
        deleteRecord: function (record) {
            var self = this;
            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this record!",
                icon: "warning",
                buttons: {
                    cancel: "Cancel",
                    yes: {
                        text: "Yes, Delete it!",
                        value: true,
                        className: "btn-danger",
                        closeModal: false
                    }
                },
                dangerMode: true
            }).then(function (willDelete) {
                if (willDelete) {
                    self.$http.delete('admin/user/{0}/'.f(record.id)).then(function (response) {
                        swal.stopLoading();
                        swal.close();
                        self.showSuccess('Record deleted successfully', 5000);
                        EventsBus.$emit('admin-users:table-updated');
                    }, function (error) {
                        swal.stopLoading();
                        self.showDefaultServerError(error);
                    });
                }
            });
        }
    }
});

const BaseAdminUserMixin = {
    components: {
        Multiselect: VueMultiselect.default
	},
    data: function () {
        return {
            saving: false,
            record: {
                _groups: [], groups: [], _user_permissions: [], user_permissions: [],
                is_staff: true, is_superuser: false, is_active: true
            }
        }
    },
    watch: {
        'record._groups': function (val, oldVal) {
            this.record.groups = val.map(function (g) {
                return g.id;
            });
        },
        'record._user_permissions': function (val, oldVal) {
            this.record.user_permissions = val.map(function (p) {
                return p.id;
            });
        }
    }
};

const AdminNewUser = Vue.component('new-admin-user', {
    template: '#admin-user-form-template',
    mixins: [UtilMixin, LoadingOverlayableMixin, BaseAdminUserMixin],
    methods: {
        saveRecord: function () {
            var self = this;
            self.saving = true;
            this.$http.post('admin/user', this.record).then(function(response) {
                self.saving = false;
                self.showSuccess('User added successfully', 5000);
                self.$router.push({name: 'admin_users'});
                EventsBus.$emit('admin-users:table-updated');
            }, function(error) {
                self.saving = false;
                self.showDefaultServerError(error);
            });
        }
    }
});

const AdminEditUser = Vue.component('edit-admin-user', {
    template: '#admin-user-form-template',
    mixins: [UtilMixin, LoadingOverlayableMixin, BaseAdminUserMixin],
    created: function() {
        var self = this,
            recordId = this.$route.params.record_id;
        this.loadingOverlay = true;
        this.$http.get('admin/user/{0}/'.f(recordId)).then(function (response) {
            self.loadingOverlay = false;
            self.record = response.data;
        }, function (error) {
            self.loadingOverlay = false;
            self.showDefaultServerError(error)
        });
    },
    methods: {
        saveRecord: function () {
            var self = this,
                recordId = this.$route.params.record_id;
            self.saving = true;
            this.$http.put('admin/user/{0}/'.f(recordId), this.record).then(function(response) {
                self.saving = false;
                self.showSuccess('User updated successfully', 5000);
                self.$router.push({name: 'admin_users'});
                EventsBus.$emit('admin-users:table-updated');
            }, function(error) {
                self.saving = false;
                self.showDefaultServerError(error);
            });
        }
    }
});

const AdminChangePasswordUser = Vue.component('change-password-admin-user', {
    template: '#admin-user-change-password-template',
    mixins: [UtilMixin, LoadingOverlayableMixin],
    data: function () {
        return {
            changingPassword: false,
            userPassword: {
                password: '', re_password: ''
            }
        }
    },
    created: function() {
        var self = this,
            recordId = this.$route.params.record_id;
        this.loadingOverlay = true;
        this.$http.get('admin/user/{0}/'.f(recordId)).then(function (response) {
            self.loadingOverlay = false;
            self.record = response.data;
        }, function (error) {
            self.loadingOverlay = false;
            self.showDefaultServerError(error)
        });
    },
    computed: {
        passwordMatched: function () {
            return this.userPassword.password === this.userPassword.re_password;
        }
    },
    methods: {
        changePassword: function () {
            var self = this,
                recordId = this.$route.params.record_id;
            self.changingPassword = true;
            this.$http.put('admin/user/{0}/set_password'.f(recordId), self.userPassword).then(function(response) {
                self.changingPassword = false;
                self.showSuccess('Password Change successfully', 5000);
                self.$router.push({name: 'admin_edit_user', params: {record_id: recordId}});
            }, function(error) {
                self.changingPassword = false;
                self.showDefaultServerError(error);
            });
        }
    }
});

const AdminGroups = Vue.component('admin-groups', {
    template: '#admin-group-list-template',
    mixins: [UtilMixin, VuetableBootstrapMixin],
    data: function () {
        return {
            tableUrl: '/api/v1/admin/group/',
            tablePerPage: 0,
            tableFiltering: {
                pattern: null
            },
            tableFields: [
                {name: 'id', sortField: 'id', title: 'ID#', callback: 'idFormat'},
                {name: '__slot:name', sortField: 'name', title: 'Name', callback: 'nameFormat'},
                {name: 'permissions', title: 'Permissions', callback: 'permissionsFormat'},
                '__slot:actions'
            ]
        }
    },
    mounted: function () {
        EventsBus.$on('admin-groups:table-updated', this.onUpdatedEvent);
    },
    destroyed: function () {
        EventsBus.$off('admin-groups:table-updated', this.onUpdatedEvent);
    },
    methods: {
        onUpdatedEvent: function () {
            this.$refs.vuetable.refresh();
        },
        idFormat: function (value) {
            return '<span class="text-primary">{0}</span>'.f(value);
        },
        nameFormat: function (value) {
            return '<span class="text-primary">{0}</span>'.f(value);
        },
        permissionsFormat: function (value) {
            return '<span class=""><strong>{0}</strong></strong> Permissions</span>'.f(value.length);
        },
        clearFilters: function () {
            this.tableFiltering = {
                pattern: null
            };
        },
        deleteRecord: function (record) {
            var self = this;
            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this record!",
                icon: "warning",
                buttons: {
                    cancel: "Cancel",
                    yes: {
                        text: "Yes, Delete it!",
                        value: true,
                        className: "btn-danger",
                        closeModal: false
                    }
                },
                dangerMode: true
            }).then(function (willDelete) {
                if (willDelete) {
                    self.$http.delete('admin/group/{0}/'.f(record.id)).then(function (response) {
                        swal.stopLoading();
                        swal.close();
                        self.showSuccess('Record deleted successfully', 5000);
                        EventsBus.$emit('admin-groups:table-updated');
                    }, function (error) {
                        swal.stopLoading();
                        self.showDefaultServerError(error);
                    });
                }
            });
        }
    }
});

const BaseAdminGroupMixin = {
    components: {
        Multiselect: VueMultiselect.default
    },
    data: function () {
        return {
            saving: false,
            record: {
                _permissions: [], permissions: []
            }
        }
    },
    watch: {
        'record._permissions': function (val, oldVal) {
            this.record.permissions = val.map(function (p) {
                return p.id;
            });
        }
    }
};

const AdminNewGroup = Vue.component('new-admin-group', {
    template: '#admin-group-form-template',
    mixins: [UtilMixin, LoadingOverlayableMixin, BaseAdminGroupMixin],
    methods: {
        saveRecord: function () {
            var self = this;
            self.saving = true;
            this.$http.post('admin/group', this.record).then(function(response) {
                self.saving = false;
                self.showSuccess('Group added successfully', 5000);
                self.$router.push({name: 'admin_groups'});
                EventsBus.$emit('admin-groups:table-updated');
            }, function(error) {
                self.saving = false;
                self.showDefaultServerError(error);
            });
        }
    }
});

const AdminEditGroup = Vue.component('edit-admin-group', {
    template: '#admin-group-form-template',
    mixins: [UtilMixin, LoadingOverlayableMixin, BaseAdminGroupMixin],
    created: function() {
        var self = this,
            recordId = this.$route.params.record_id;
        this.loadingOverlay = true;
        this.$http.get('admin/group/{0}/'.f(recordId)).then(function (response) {
            self.loadingOverlay = false;
            self.record = response.data;
        }, function (error) {
            self.loadingOverlay = false;
            self.showDefaultServerError(error)
        });
    },
    methods: {
        saveRecord: function () {
            var self = this,
                recordId = this.$route.params.record_id;
            self.saving = true;
            this.$http.put('admin/group/{0}/'.f(recordId), this.record).then(function(response) {
                self.saving = false;
                self.showSuccess('Group updated successfully', 5000);
                self.$router.push({name: 'admin_groups'});
                EventsBus.$emit('admin-groups:table-updated');
            }, function(error) {
                self.saving = false;
                self.showDefaultServerError(error);
            });
        }
    }
});

/****************************************
 ***************** Router ***************
 ****************************************/
const ADMIN_ROUTE_PREFIX = '/admin';
const adminRoutes = [
    {
        path: '{0}/'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_root',
        redirect: {name: 'admin_dashboard'}
    }, {
        path: '{0}/dashboard'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_dashboard',
        meta: {
            pageInfo: {
                title: 'Admin Dashboard',
                titleDesc: 'reports & statistics'
            }
        },
        component: Dashboard
    }, {
        path: '{0}/myprofile'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_myprofile',
        meta: {
            pageInfo: {
                title: 'My Profile',
                titleDesc: 'user account info'
            }
        },
        component: MyProfile
    }, {
        path: '{0}/users'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_users',
        meta: {
            pageInfo: {
                title: 'Users List',
                titleDesc: 'list of users'
            }
        },
        component: AdminUsers
    }, {
        path: '{0}/users/new'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_new_user',
        meta: {
            pageInfo: {
                title: 'New User',
                titleDesc: 'add new user',
                back: 'admin_users'
            }
        },
        component: AdminNewUser
    }, {
        path: '{0}/users/:record_id/edit'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_edit_user',
        meta: {
            pageInfo: {
                title: 'Edit User',
                titleDesc: 'edit existing user',
                back: 'admin_users'
            }
        },
        component: AdminEditUser
    }, {
        path: '{0}/users/:record_id/change-password'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_change_password_user',
        meta: {
            pageInfo: {
                title: 'Change Password',
                titleDesc: 'change password of user'
            }
        },
        component: AdminChangePasswordUser
    }, {
        path: '{0}/groups'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_groups',
        meta: {
            pageInfo: {
                title: 'Groups List',
                titleDesc: 'list of groups'
            }
        },
        component: AdminGroups
    }, {
        path: '{0}/groups/new'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_new_group',
        meta: {
            pageInfo: {
                title: 'New Group',
                titleDesc: 'add new group',
                back: 'admin_groups'
            }
        },
        component: AdminNewGroup
    }, {
        path: '{0}/groups/:record_id/edit'.f(ADMIN_ROUTE_PREFIX),
        name: 'admin_edit_group',
        meta: {
            pageInfo: {
                title: 'Edit Group',
                titleDesc: 'edit existing Group',
                back: 'admin_groups'
            }
        },
        component: AdminEditGroup
    }
];
const defaultRoutes = [
    {
        path: '/',
        name: 'root',
        redirect: {name: 'dashboard'}
    }, {
        path: '/dashboard',
        name: 'dashboard',
        meta: {
            pageInfo: {
                title: 'Dashboard',
                titleDesc: 'reports & statistics'
            }
        },
        component: Dashboard
    }, {
        path: '/exclude-patterns',
        name: 'exclude_patterns',
        meta: {
            pageInfo: {
                title: 'Exclude Patterns',
                titleDesc: 'list of excluded pattern files'
            }
        },
        component: ExcludePatterns
    }, {
        path: '/exclude-patterns/new',
        name: 'new_exclude_pattern',
        meta: {
            pageInfo: {
                title: 'New Exclude Pattern',
                titleDesc: 'add new exclude pattern',
                back: 'exclude_patterns'
            }
        },
        component: NewExcludePattern
    }, {
        path: '/exclude-patterns/:record_id/edit',
        name: 'edit_exclude_pattern',
        meta: {
            pageInfo: {
                title: 'Edit Exclude Pattern',
                titleDesc: 'edit existing exclude pattern',
                back: 'exclude_patterns'
            }
        },
        component: EditExcludePattern
    }, {
        path: '/myprofile',
        name: 'myprofile',
        meta: {
            pageInfo: {
                title: 'My Profile',
                titleDesc: 'user account info'
            }
        },
        component: MyProfile
    }
];
const router = new VueRouter({
    routes: defaultRoutes.concat(adminRoutes)
});
router.beforeResolve(function (toRoute, fromRoute, next) {
    if (toRoute.matched.length) {
        next();
    } else {
        var isAdmin = (toRoute.name || '').startsWith('admin_') || (toRoute.fullPath || '').startsWith('{0}/'.f(ADMIN_ROUTE_PREFIX));
        next({name: isAdmin ? 'admin_root' : 'root'});
    }
});
router.afterEach(function(toRoute, fromRoute) {
    if (toRoute.fullPath.startsWith('{0}/'.f(ADMIN_ROUTE_PREFIX))) {
        if (store.getters.isLoadedUser && !store.getters.isStaffUser) {
            return router.replace({'name': 'root'});
        }
        store.dispatch('switchAdminView');
    } else {
        store.dispatch('switchUserView');
    }
    var title = 'Co Database :: ',
        pageInfo = toRoute.meta.pageInfo || {};
    if (pageInfo.title) {
        title = title + pageInfo.title + ' :: ';
    }
    if (pageInfo.titleDesc) {
        title = title + pageInfo.titleDesc;
    }
    window.document.title = title;
});

const store = new Vuex.Store({
    state: {
        currentUser: {},
        viewType: 'user',
        currentCounty: null,
        counties: null,
        groups: null,
        permissions: null
    },
    actions: {
        switchUserView: function(state) {
            store.state.viewType = 'user';
        },
        switchAdminView: function(state) {
            store.state.viewType = 'admin';
        }
    },
    getters: {
        isUserViewType: function (state) {
            return state.viewType === 'user';
        },
        isAdminViewType: function (state) {
            return state.viewType === 'admin';
        },
        isStaffUser: function (state) {
            return true === state.currentUser.is_staff;
        },
        isLoadedUser: function (state) {
            return !!state.currentUser.id;
        },
        getCurrentCounty: function (state) {
            if (state.currentCounty === null) {
                state.currentCounty = (state.counties || [])[0] || null;
            }
            return state.currentCounty;
        },
        allCounties: function(state) {
            if (state.counties === null) {
                Vue.prototype.$http.get('county', {params: {ordering: 'id'}}).then(function(response) {
                    state.counties = response.data;
                }, function(error) {
                    app.showDefaultServerError(error);
                });
            }
            return state.counties || [];
        },
        allGroups: function(state) {
            if (state.groups === null) {
                Vue.prototype.$http.get('admin/group', {params: {page_size: 0, fields: 'id,name'}}).then(function(response) {
                    state.groups = response.data.results;
                }, function(error) {
                    app.showDefaultServerError(error);
                });
            }
            return state.groups || [];
        },
        allPermissions: function(state) {
            if (state.permissions === null) {
                Vue.prototype.$http.get('admin/permission', {params: {page_size: 0}}).then(function(response) {
                    state.permissions = response.data.results;
                }, function(error) {
                    app.showDefaultServerError(error);
                });
            }
            return state.permissions || [];
        }
    }
});

const EventsBus = new Vue();

/****************************************
 ****************** App *****************
 ****************************************/
axios.defaults.baseURL = '/api/v1';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
axios.interceptors.request.use(function (request) {
    if (request.method === 'get') {
        var r = UtilMixin.methods.randomId();
        request.url = UtilMixin.methods.addQSParm(request.url, 'nc', r);
    }
    return request;
});
axios.defaults.paramsSerializer = function(params) {
    return Qs.stringify(params, {arrayFormat: 'repeat'});
};
Vue.prototype.$http = axios;
var app = new Vue({
    el: '#co_database-app',
    store: store,
    router: router,
    data: {},
    mixins: [UtilMixin],
    methods: {},
    filters: {},
    created: function () {
        var self = this;
        this.$http.get('me').then(function (response) {
            store.state.currentUser = response.data;
            if (!store.getters.isStaffUser) {
                router.replace({'name': 'root'});
            }
            $('body').css('background-image', 'none').removeClass('hide');
        }, function (error) {
            self.showDefaultServerError(error);
        });
    },
    mounted: function () {
        Metronic.init(); // init metronic core componets
        Layout.init(); // init layout
        Index.init();
    }
});
