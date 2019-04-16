from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from ast import literal_eval
from collections import Counter
from itertools import chain
from random import shuffle
from .tokens import account_activation_token
from .forms import AssessmentForm, AttributeForm, AttributeOptionForm, CoordinatesForm, DataForm, EAVExperimentForm, EAVOutcomeForm, EAVPopulationForm, EAVPublicationForm, ExperimentForm, ExperimentDateForm, ExperimentDesignForm, ExperimentPopulationForm, ExperimentPopulationOutcomeForm, FullTextAssessmentForm, InterventionForm, OutcomeForm, ProfileForm, PublicationForm, PublicationDateForm, PublicationPopulationForm, PublicationPopulationOutcomeForm, SignUpForm, UserForm, XCountryForm
from .models import Assessment, AssessmentStatus, Attribute, Coordinates, Country, Crop, Data, Design, EAV, Experiment, ExperimentCrop, ExperimentDate, ExperimentDesign, ExperimentPopulation, ExperimentPopulationOutcome, Intervention, Outcome, Publication, PublicationDate, PublicationPopulation, PublicationPopulationOutcome, Subject, User, UserSubject, XCountry
from .serializers import AttributeSerializer, CountrySerializer, DataSerializer, DesignSerializer, EAVSerializer, ExperimentSerializer, ExperimentDesignSerializer, ExperimentPopulationSerializer, ExperimentPopulationOutcomeSerializer, InterventionSerializer, OutcomeSerializer, PublicationSerializer, PublicationPopulationSerializer, PublicationPopulationOutcomeSerializer, SubjectSerializer, UserSerializer
from .decorators import group_required
from mptt.forms import TreeNodeChoiceField
from haystack.generic_views import SearchView
from haystack.forms import SearchForm
from haystack.query import SearchQuerySet
from rest_framework import viewsets
from django_filters import rest_framework as filters
import reversion
import csv
import json


class AttributeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user-defined attributes (for the EAV model)
    """
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer

    def get_queryset(self):
        queryset = Attribute.objects.all()
        parent_pk = self.request.GET.get('parent', '')
        if parent_pk is not '':
            queryset = Attribute.objects.get(pk=parent_pk).get_children()
        return queryset


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "countries"
    """
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class DesignViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "designs"
    """
    queryset = Design.objects.all()
    serializer_class = DesignSerializer


class EAVViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "EAVs" (entity-attribute-values: user-defined fields)
    """
    queryset = EAV.objects.all()
    serializer_class = EAVSerializer


class ExperimentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "experiments" (i.e. one "intervention" in one "publication")
    """
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer


class ExperimentDesignViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "experiment_designs" (i.e. one "design" element in one "experiment")
    """
    queryset = ExperimentDesign.objects.distinct()
    serializer_class = ExperimentDesignSerializer


class ExperimentPopulationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "experiment_populations" (i.e. one "population" in one "experiment")
    """
    queryset = ExperimentPopulation.objects.all()
    serializer_class = ExperimentPopulationSerializer


class ExperimentPopulationOutcomeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "experiment populations outcomes" (i.e. one "outcome" for one "population" in one "experiment")
    """
    queryset = ExperimentPopulationOutcome.objects.all()
    serializer_class = ExperimentPopulationOutcomeSerializer


class DataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for data (e.g., treatment mean, control mean, etc.)
    """
    queryset = Data.objects.all()
    serializer_class = DataSerializer

    def get_queryset(self):
        queryset = Data.objects.all()
        subject_pk = self.request.GET.get('subject', '')
        if subject_pk is not '':
            subject = Subject.objects.get(pk=subject_pk)
            queryset = queryset.filter(subject=subject)
        intervention_pk = self.request.GET.get('intervention', '')
        if intervention_pk is not '':
            interventions = Intervention.objects.get(pk=intervention_pk).get_descendants(include_self=True)
            queryset = queryset.filter(experiment__intervention__in=interventions)
        outcome_pk = self.request.GET.get('outcome', '')
        if outcome_pk is not '':
            outcomes = Outcome.objects.get(pk=outcome_pk).get_descendants(include_self=True)
            queryset = queryset.filter(experiment_population_outcome__outcome__in=outcomes)
        return queryset


class InterventionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "interventions"
    """
    queryset = Intervention.objects.all()
    serializer_class = InterventionSerializer


class OutcomeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "outcomes"
    """
    queryset = Outcome.objects.all()
    serializer_class = OutcomeSerializer


class PublicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "publications"
    """
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer


class PublicationPopulationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "publication_populations" (i.e. one "population" in one "publication")
    """
    queryset = PublicationPopulation.objects.all()
    serializer_class = PublicationPopulationSerializer


class PublicationPopulationOutcomeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "publication_population_outcomes" (i.e. one "outcome" for one "population" in one "publication")
    """
    queryset = PublicationPopulationOutcome.objects.all()
    serializer_class = PublicationPopulationOutcomeSerializer


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "subjects"
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    def get_queryset(self):
        queryset = Subject.objects.all()
        subject_pk = self.request.GET.get('subject', '')
        if subject_pk is not '':
            subject = Subject.objects.get(pk=subject_pk)
            queryset = queryset.filter(subject=subject)
        return queryset


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for "users"
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class MySearchView(SearchView):
    template_name = 'search/search.html'

    def get_queryset(self, *args, **kwargs):
        subject = self.kwargs['subject']
        subject = Subject.objects.get(slug=subject)
        queryset = super(MySearchView, self).get_queryset()
        return queryset.filter(subject=subject)

    def get_context_data(self, *args, **kwargs):
        context = super(MySearchView, self).get_context_data(*args, **kwargs)
        # do something
        return context


def subject(request, subject):
    user = request.user
    subject = Subject.objects.get(slug=subject)
    context = {
        'subject': subject
    }
    # Get data for the sidebar.
    if user.is_authenticated:
        if Publication.objects.filter(subject=subject).exists():
            status = get_status(user, subject)
            context.update(status)
    return render(request, 'publications/subject.html', context)


def publications(request, subject, state='all', download='none'):
    user = request.user
    subject = Subject.objects.get(slug=subject)
    # All publications
    if (state == 'all'):
        publications = Publication.objects.filter(subject=subject).order_by('title')
    # Publications that this user has assessed as relevant based on title/abstract
    elif (state == 'relevant'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                is_relevant=True
            )
        ).order_by('title')
    # Publications that this user has assessed as not relevant based on title/abstract
    elif (state == 'not_relevant'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                is_relevant=False
            )
        ).order_by('title')
    # Publications that this user has not yet assessed based on title/abstract
    elif (state == 'not_assessed'):
        publications = Publication.objects.distinct().filter(subject=subject).exclude(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user
            )
        ).order_by('title')
    # Publications that this user has assessed as relevant based on full text
    elif (state == 'relevant_full_texts'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                is_relevant=True,  # is_relevant based on title/abstract
                full_text_is_relevant=True
            )
        ).order_by('title')
    # Publications that this user has assessed as not relevant based on full text
    elif (state == 'not_relevant_full_texts'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                is_relevant=True,  # is_relevant based on title/abstract
                full_text_is_relevant=False
            )
        ).order_by('title')
    # Cannot find
    elif (state == 'cannot_find'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                cannot_find = True
            )
        ).order_by('title')
    # Cannot find
    elif (state == 'cannot_access'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                cannot_access = True
            )
        ).order_by('title')
    elif (state == 'secondary_literature'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                secondary_literature = True
            )
        ).order_by('title')
    elif (state == 'other'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                other = True
            )
        ).order_by('title')
    elif (state == 'no_pico'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user
            ).filter(
                Q(no_population=True) |
                Q(no_intervention=True) |
                Q(no_comparator=True) |
                Q(no_outcome=True)
            )
        ).order_by('title')
    # Publications that this user has marked as completed
    elif (state == 'completed'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                is_completed=True
            )
        ).order_by('title')
    # Publications that this user has not yet assessed based on full text
    elif (state == 'not_assessed_full_texts'):
        publications = Publication.objects.distinct().filter(
            assessment__in=Assessment.objects.filter(
                subject=subject,
                user=user,
                is_relevant=True,  # is_relevant based on title/abstract
                full_text_is_relevant=None
            )
        ).order_by('title')
    # If the request is to download the publications, rather than viewing them online
    if download == 'CSV':
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="bibliography.csv"'
        # Write the CSV
        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(['Authors', 'Year', 'Title', 'Journal', 'Volume', 'Issue', 'DOI', 'URL', 'Abstract'])
        slug = subject.slug
        current_site = get_current_site(request)
        domain = current_site.domain
        for publication in publications:
            try:
                separator = ', '
                authors = separator.join(publication.author_list)
            except:
                authors = publication.authors
            path = reverse('publication', args=(), kwargs={'subject': slug, 'publication_pk': publication.pk})
            url = "http://{domain}{path}".format(domain=domain, path=path)
            writer.writerow([authors, publication.year, publication.title, publication.journal, publication.volume, publication.issue, publication.doi, url, publication.abstract])
        return response
    # If the request is not to download the publications
    page = request.GET.get('page', 1)
    paginator = Paginator(publications, 10)
    try:
        publications = paginator.page(page)
    except PageNotAnInteger:
        publications = paginator.page(1)
    except EmptyPage:
        publications = paginator.page(paginator.num_pages)
    context = {
        'subject': subject,
        'publications': publications
    }
    if user.is_authenticated:
        status = get_status(user, subject)
        context.update(status)
    return render(request, 'publications/publications.html', context)


def home(request):
    return render(request, 'publications/home.html')


def about(request):
    return render(request, 'publications/about.html')


def methods(request):
    return render(request, 'publications/methods.html')


def contact(request):
    return render(request, 'publications/contact.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():

            """
            ''' Begin reCAPTCHA validation '''

            recaptcha_response = request.POST.get('g-recaptcha-response')
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                'secret': config.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response
            }
            data = urllib.parse.urlencode(values).encode()
            req =  urllib.request.Request(url, data=data)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode())

            ''' End reCAPTCHA validation '''
            """

#            if result['success']:
            user = form.save()
            user.refresh_from_db()  # Load the profile instance created by the signal.
            user.profile.institution = form.cleaned_data.get('institution')
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Metadataset'
            message = render_to_string('publications/confirm_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('email_sent')
    else:
        form = SignUpForm()
    return render(request, 'publications/signup.html', {'form': form})


def email_sent(request):
    return render(request, 'publications/email_sent.html')


def email_confirmed(request):
    return render(request, 'publications/email_confirmed.html')


def email_not_confirmed(request):
    return render(request, 'publications/email_not_confirmed.html')


def confirm_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_is_confirmed = True
        user.save()
        login(request, user)
        return render(request, 'publications/email_confirmed.html')
    else:
        return render(request, 'publications/email_not_confirmed.html', {'uid': uid})


@login_required
@transaction.atomic
def profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.first_name = user_form.cleaned_data.get('first_name')
            user.last_name = user_form.cleaned_data.get('last_name')
            user.profile.institution = profile_form.cleaned_data.get('institution')
            user.save()
            return render(request, 'publications/profile_updated.html')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, 'publications/profile.html', context)


@login_required
def publication(request, subject, publication_pk):
    """
    On this page, the user chooses interventions for this publication.
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    intervention = subject.intervention  # The root intervention for this subject (each subject can have its own classification of interventions)
    publication_pk = int(publication_pk)
    # This publication
    publication = get_object_or_404(Publication, pk=publication_pk, subject=subject)
    # Get data for the sidebar.
    status = get_status(user, subject)
    item = status.get('item')  # item = AssessmentStatus instance for this user and subject
    assessment_order = literal_eval(item.assessment_order)
    completed_assessments = literal_eval(item.completed_assessments)

    # The next pk and previous pk in assessment_order, to be used for navigation
    try:
        previous_pk = assessment_order[assessment_order.index(publication_pk) - 1]
    except:
        previous_pk = assessment_order[0]
    try:
        next_pk = assessment_order[assessment_order.index(publication_pk) + 1]
    except:
        next_pk = assessment_order[0]

    # "next_assessment" is the next pk in assessment_order that has not yet been assessed (whereas "next_pk" may or may not have been assessed).
    next_assessment = item.next_assessment
    if next_assessment == publication_pk:  # Users can pass from this "next_assessment" to the next "next_assessment".
        next_assessment = get_next_assessment(publication_pk, next_pk, assessment_order, completed_assessments)
        item.next_assessment = next_assessment
        item.save()

    ExperimentFormSet = modelformset_factory(Experiment, form=ExperimentForm, extra=4, can_delete=True)
    # Form for this assessment
    if Assessment.objects.filter(publication=publication, user=user, subject=subject).exists():
        assessment = Assessment.objects.get(publication=publication, user=user, subject=subject)
        assessment_form = AssessmentForm(data=data, instance=assessment, prefix="assessment_form")
        full_text_assessment_form = FullTextAssessmentForm(data=data, instance=assessment, prefix="full_text_assessment_form")
        # Get relevance for context.
        if assessment.is_relevant == True:
            is_relevant = 'True'
        else:
            is_relevant = 'False'
        if assessment.full_text_is_relevant == True:
            full_text_is_relevant = 'True'
        elif assessment.full_text_is_relevant == False:
            full_text_is_relevant = 'False'
        else:
            full_text_is_relevant = ''  # Not yet assessed
    else:
        assessment_form = AssessmentForm(data=data, prefix="assessment_form")
        full_text_assessment_form = FullTextAssessmentForm(data=data, prefix="full_text_assessment_form")
        is_relevant = ''  # Not yet assessed
        full_text_is_relevant = ''  # Not yet assessed

    # Formset for this publication
    formset = ExperimentFormSet(data=data, queryset=Experiment.objects.filter(publication=publication), prefix="experiment_formset")
    if request.method == 'POST':
        if 'is_relevant' in request.POST:
            with transaction.atomic():
                # Update assessment
                if assessment_form.is_valid():
                    assessment = assessment_form.save(commit=False)
                    assessment.user = user
                    assessment.publication = publication
                    assessment.subject = subject
                    assessment.is_relevant = True
                    assessment.is_completed = False
                    assessment.full_text_is_relevant = None
                    assessment.cannot_find = False
                    assessment.cannot_access = False
                    assessment.secondary_literature = False
                    assessment.no_population = False
                    assessment.no_intervention = False
                    assessment.no_outcome = False
                    assessment.no_comparator = False
                    assessment.other = False
                    assessment.note = ''
                    assessment.save()
                    # Update status and get next assessment
                    if publication_pk not in completed_assessments:
                        completed_assessments.append(publication_pk)
                        item.completed_assessments = completed_assessments
                    next_assessment = get_next_assessment(publication_pk, next_pk, assessment_order, completed_assessments)
                    item.next_assessment = next_assessment
                    item.save()
                    return redirect('publication', subject=subject.slug, publication_pk=next_assessment)
        if 'is_not_relevant' in request.POST:
            with transaction.atomic():
                if assessment_form.is_valid():
                    # Update assessment
                    assessment = assessment_form.save(commit=False)
                    assessment.user = user
                    assessment.publication = publication
                    assessment.subject = subject
                    assessment.is_relevant = False
                    assessment.is_completed = False
                    assessment.full_text_is_relevant = None
                    assessment.cannot_find = False
                    assessment.cannot_access = False
                    assessment.secondary_literature = False
                    assessment.no_population = False
                    assessment.no_intervention = False
                    assessment.no_outcome = False
                    assessment.no_comparator = False
                    assessment.other = False
                    assessment.note = ''
                    assessment.save()
                    # Update status and get next assessment
                    if publication_pk not in completed_assessments:
                        completed_assessments.append(publication_pk)
                        item.completed_assessments = completed_assessments
                    next_assessment = get_next_assessment(publication_pk, next_pk, assessment_order, completed_assessments)
                    item.next_assessment = next_assessment
                    item.save()
                    return redirect('publication', subject=subject.slug, publication_pk=next_assessment)
        if 'full_text_is_not_relevant' in request.POST:
            with transaction.atomic():
                if full_text_assessment_form.is_valid():
                    # Update assessments (add the reason for rejection)
                    assessment = full_text_assessment_form.save(commit=False)
                    assessment.user = user
                    assessment.publication = publication
                    assessment.subject = subject
                    assessment.is_relevant = True  # It must be relevant based on the title and abstract if it is to be rejected based on the full text.
                    assessment.is_completed = True
                    assessment.full_text_is_relevant = False
                    assessment.save()
                    # Update status and get next assessment
                    if publication_pk not in completed_assessments:
                        completed_assessments.append(publication_pk)
                        item.completed_assessments = completed_assessments
                    next_assessment = get_next_assessment(publication_pk, next_pk, assessment_order, completed_assessments)
                    item.next_assessment = next_assessment
                    item.save()
                return redirect('publication', subject=subject.slug, publication_pk=publication_pk)
        if 'save' in request.POST or 'delete' in request.POST:
            with transaction.atomic():
                # Before the formset is validated, the choices need to be redefined, or the validation will fail. This is because only a subset of all choices (high level choices in the MPTT tree) were initially shown in the dropdown (for better UI).
                interventions = TreeNodeChoiceField(queryset=Intervention.objects.filter(pk=intervention.pk).get_descendants(include_self=True), level_indicator = "---")
                for form in formset:
                    form.fields['intervention'] = interventions
                if formset.is_valid():
                    instances = formset.save(commit=False)
                    if 'delete' in request.POST:
                        for obj in formset.deleted_objects:
                            obj.delete()
                    else:
                        for instance in instances:
                            instance.publication = publication
                            instance.user = user
                            instance.save()
                    if full_text_assessment_form.is_valid():
                        # If an intervention has been selected, mark this publication as "relevant" to this systematic map.
                        # Check if this publication was already marked as "completed" before saving the form. If it was, mark it as not "completed" (because a new intervention has been added, and the user will need to add new metadata).
                        if Experiment.objects.filter(publication=publication, user=user).exists():
                            if Assessment.objects.filter(publication=publication, user=user).exists():
                                old_assessment = Assessment.objects.get(publication=publication, user=user)
                                was_completed = old_assessment.is_completed
                            else:
                                was_completed = False
                            # Get the form data for the new assessment.
                            assessment = full_text_assessment_form.save(commit=False)
                            if was_completed == True:
                                assessment.is_completed = False
                            else:
                                assessment.is_completed = assessment.is_completed
                            assessment.user = user
                            assessment.publication = publication
                            assessment.subject = subject
                            assessment.is_relevant = True
                            assessment.full_text_is_relevant = True
                            assessment.cannot_find = False
                            assessment.cannot_access = False
                            assessment.secondary_literature = False
                            assessment.no_population = False
                            assessment.no_intervention = False
                            assessment.no_outcome = False
                            assessment.no_comparator = False
                            assessment.other = False
                            assessment.note = ''
                            assessment.save()
                            # Update status and get next assessment
                            if publication_pk not in completed_assessments:
                                completed_assessments.append(publication_pk)
                                item.completed_assessments = completed_assessments
                            next_assessment = get_next_assessment(publication_pk, next_pk, assessment_order, completed_assessments)
                            item.next_assessment = next_assessment
                            item.save()
                        # If all interventions have been deleted, remove this publication from the completed assessments.
                        elif 'delete' in request.POST:
                            if publication_pk in completed_assessments:
                                completed_assessments.remove(publication_pk)
                                item.completed_assessments = completed_assessments
                            next_assessment = publication_pk
                            item.next_assessment = next_assessment
                            item.save()
                            if Assessment.objects.filter(publication=publication, user=user).exists():
                                Assessment.objects.filter(publication=publication, user=user).delete()
                return redirect('publication', subject=subject.slug, publication_pk=publication_pk)
    else:
        # Intervention choices for the formset (high-level choices only)
        interventions = TreeNodeChoiceField(required=False, queryset=Intervention.objects.filter(pk=intervention.pk).get_descendants(include_self=True).filter(level__lte=2).filter(level__gt=0), level_indicator = "---")
        for form in formset:
            form.fields['intervention'] = interventions
    context = {
        'subject': subject,
        'publication': publication,
        'assessment_form': assessment_form,
        'full_text_assessment_form': full_text_assessment_form,
        'experiment_formset': formset,
        'is_relevant': is_relevant,
        'full_text_is_relevant': full_text_is_relevant,
        'next_pk': next_pk,
        'previous_pk': previous_pk
    }
    status = get_status(user, subject)
    context.update(status)
    return render(request, 'publications/publication.html', context)


@login_required
def metadata(request, subject, publication_pk):
    """
    On this page, the user edits the publication-level metadata for this publication (i.e. metadata that is applicable to all interventions).
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    outcome = subject.outcome  # The root outcome for this subject (each subject can have its own classification of outcomes)
    attribute = subject.attribute  # The root attribute for this subject (each subject can have its own classification of attributes)
    attributes = Attribute.objects.get(pk=attribute.pk).get_children()
    attributes_count = attributes.count()
    # This publication
    publication = get_object_or_404(Publication, pk=publication_pk, subject=subject)
    # Formsets
    PublicationDateFormSet = modelformset_factory(PublicationDate, form=PublicationDateForm, extra=2, max_num=2, can_delete=True)
    PublicationPopulationFormSet = modelformset_factory(PublicationPopulation, form=PublicationPopulationForm, extra=4, can_delete=True)
    CoordinatesFormSet = modelformset_factory(Coordinates, form=CoordinatesForm, extra=1, can_delete=True)
    EAVFormSet = modelformset_factory(EAV, form=EAVPublicationForm, extra=attributes_count, max_num=attributes_count, can_delete=True)
    XCountryFormSet = modelformset_factory(XCountry, form=XCountryForm, extra=1, can_delete=True)
    # Formsets for this publication
    publication_date_formset = PublicationDateFormSet(data=data, queryset=PublicationDate.objects.filter(publication=publication), prefix="publication_date_formset")
    coordinates_formset = CoordinatesFormSet(data=data, queryset=Coordinates.objects.filter(publication=publication), prefix="coordinates_formset")
    x_country_formset = XCountryFormSet(data=data, queryset=XCountry.objects.filter(publication=publication), prefix="x_country_formset")
    # publication_population_formset
    publication_population_formset = PublicationPopulationFormSet(data=data, queryset=PublicationPopulation.objects.filter(publication=publication), prefix="publication_population_formset")
    populations = TreeNodeChoiceField(queryset=Outcome.objects.filter(pk=outcome.pk).get_descendants(include_self=True).filter(level=1), level_indicator = "---")
    for form in publication_population_formset:
        form.fields['population'] = populations
    # EAV_formset
    EAV_formset = EAVFormSet(data=data, queryset=EAV.objects.filter(publication=publication), prefix="EAV_formset")
    for form in EAV_formset:
        # There should only be one instance per attribute, so we need to
        # check which attributes have instances and create extra formset forms
        # only for attributes without instances.
        if form.instance.pk is not None:
            attribute = form.instance.attribute
            attributes = attributes.exclude(attribute=attribute)
            form.unit = attribute.unit
        else:
            attribute = attributes[0]
            attributes = attributes.exclude(attribute=attribute)
            form.initial['attribute'] = attribute
            form.initial['publication'] = publication  # For unique_together validation
            form.initial['user'] = user  # For unique_together validation
            form.unit = attribute.unit
        if attribute.is_leaf_node():  # If factor options have not been defined, or if the data type is a number, not a factor
            form.fields['value_as_factor'].disabled = True
        else:  # If factor options have been defined (which is not possible if the data type is a number)
            form.fields['value_as_number'].disabled = True
            form.fields['value_as_factor'] = TreeNodeChoiceField(queryset=attribute.get_children(), level_indicator="")
    if request.method == 'POST':
        if 'save' in request.POST or 'delete' in request.POST:
            with transaction.atomic():
                formset = EAV_formset
                if formset.is_valid():
                    instances = formset.save(commit=False)
                    if 'delete' in request.POST:
                        for obj in formset.deleted_objects:
                            obj.delete()
                    else:
                        for instance in instances:
                            instance.publication = publication
                            instance.user = user
                            instance.publication_index = publication
                            instance.save()
                formset = x_country_formset
                if formset.is_valid():
                    instances = formset.save(commit=False)
                    if 'delete' in request.POST:
                        for obj in formset.deleted_objects:
                            obj.delete()
                    else:
                        for instance in instances:
                            instance.publication = publication
                            instance.publication_index = publication
                            instance.user = user
                            instance.save()
                formset = publication_date_formset
                if formset.is_valid():
                    instances = formset.save(commit=False)
                    if 'delete' in request.POST:
                        for obj in formset.deleted_objects:
                            obj.delete()
                    else:
                        for instance in instances:
                            instance.publication = publication
                            instance.user = user
                            instance.save()
                formset = coordinates_formset
                if formset.is_valid():
                    instances = formset.save(commit=False)
                    if 'delete' in request.POST:
                        for obj in formset.deleted_objects:
                            obj.delete()
                    else:
                        for instance in instances:
                            instance.publication = publication
                            instance.publication_index = publication
                            instance.user = user
                            instance.save()
                formset = publication_population_formset
                if formset.is_valid():
                    instances = formset.save(commit=False)
                    if 'delete' in request.POST:
                        for obj in formset.deleted_objects:
                            obj.delete()
                    else:
                        for instance in instances:
                            instance.publication = publication
                            instance.user = user
                            instance.save()
                return redirect('metadata', subject=subject.slug, publication_pk=publication_pk)
    context = {
        'subject': subject,
        'publication': publication,
        'publication_date_formset': publication_date_formset,
        'publication_population_formset': publication_population_formset,
        'x_country_formset': x_country_formset,
        'coordinates_formset': coordinates_formset,
        'EAV_formset': EAV_formset
    }
    return render(request, 'publications/metadata.html', context)


@login_required
def attributes(request, subject):
    """
    On this page, the user adds/edits attributes for this subject.
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    attribute = subject.attribute  # The root attribute for this subject (each subject can have its own classification of attributes)
    attributes = Attribute.objects.get(pk=attribute.pk).get_children()
    FormSet = modelformset_factory(Attribute, form=AttributeForm, extra=1, can_delete=True)
    formset = FormSet(data=data, queryset=attributes, initial=[{'parent': attribute}])  # To check for unique_together = ('attribute', 'parent'), parent needs to be passed to the formset as initial data, but it is hidden in the template and ignored in the view.
    if request.method == 'POST':
        if 'save' in request.POST or 'delete' in request.POST:
            with transaction.atomic():
                if formset.is_valid():
                    instances = formset.save(commit=False)
                    if 'delete' in request.POST:
                        for obj in formset.deleted_objects:
                            obj.delete()
                    else:
                        for instance in instances:
                            instance.parent = attribute
                            instance.user = user
                            if instance.type == 'factor':
                                instance.unit = 'NA for factors'
                            instance.save()
                return redirect('attributes', subject=subject.slug)
    context = {
        'subject': subject,
        'formset': formset
    }
    return render(request, 'publications/attributes.html', context)


@login_required
def attribute(request, subject, attribute_pk):
    """
    On this page, the user adds/edits options for this attribute.
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    attribute = Attribute.objects.get(pk=attribute_pk)
    options = attribute.get_children()
    FormSet = modelformset_factory(Attribute, form=AttributeOptionForm, extra=1, can_delete=True)
    formset = FormSet(data=data, queryset=options, initial=[{'parent': attribute}])  # To check for unique_together = ('attribute', 'parent'), parent needs to be passed to the formset as initial data, but it is hidden in the template and ignored in the view.
    if request.method == 'POST':
        if 'save' in request.POST or 'delete' in request.POST:
            with transaction.atomic():
                if formset.is_valid():
                    instances = formset.save(commit=False)
                    if 'delete' in request.POST:
                        for obj in formset.deleted_objects:
                            obj.delete()
                    else:
                        for instance in instances:
                            instance.parent = attribute
                            instance.user = user
                            instance.type = 'factor'
                            instance.save()
                return redirect('attribute', subject=subject.slug, attribute_pk=attribute_pk)
    context = {
        'subject': subject,
        'formset': formset,
        'attribute': attribute
    }
    return render(request, 'publications/attribute.html', context)


@login_required
def publication_population(request, subject, publication_pk, publication_population_index):
    """
    On this page, the user chooses an outcome for this publication population (not for a specific intervention).
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    outcome = subject.outcome  # The root outcome for this subject (each subject can have its own classification of outcomes)
    PublicationPopulationOutcomeFormSet = modelformset_factory(PublicationPopulationOutcome, form=PublicationPopulationOutcomeForm, extra=4, can_delete=True)
    # This publication
    publication = get_object_or_404(Publication, pk=publication_pk, subject=subject)
    # This publication_population
    publication_populations = PublicationPopulation.objects.filter(publication=publication).order_by('pk')
    publication_population = publication_populations[publication_population_index]
    # Formset for this publication_population
    formset = PublicationPopulationOutcomeFormSet(data=data, queryset=PublicationPopulationOutcome.objects.filter(publication_population=publication_population), prefix="publication_population_outcome_formset")
    # Outcome choices for the formset
    for form in formset:
        form.fields['outcome'] = TreeNodeChoiceField(queryset=Outcome.objects.get(pk=publication_population.population.pk).get_descendants(include_self=True), level_indicator = "---")
    if request.method == 'POST':
        with transaction.atomic():
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.publication_population = publication_population
                        instance.user = user
                        instance.save()
            return redirect('publication_population', subject=subject.slug, publication_pk=publication_pk, publication_population_index=publication_population_index)
    context = {
        'subject': subject,
        'publication': publication,
        'publication_population': publication_population,
        'publication_population_index': publication_population_index,
        'formset': formset
    }
    return render(request, 'publications/publication_population.html', context)


@login_required
def add_publication(request, subject):
    """
    On this page, the user adds a publication that has not come from a systematic search (e.g., publications from "other sources" in a PRISMA diagram).
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    publication_form = PublicationForm(data=data)
    if request.method == 'POST':
        with transaction.atomic():
            form = publication_form
            if form.is_valid():
                with reversion.create_revision():  # Version control (django-revision)
                    instance = form.save(commit=False)
                    instance.subject = subject
                    instance.is_from_systematic_search = False
                    instance.save()
                    publication_pk = instance.pk
                    reversion.set_user(request.user)
        return redirect('publication', subject=subject.slug, publication_pk=publication_pk)
    context = {
        'subject': subject,
        'publication_form': publication_form
    }
    # Get data for the sidebar.
    status = get_status(user, subject)
    context.update(status)
    return render(request, 'publications/add_publication.html', context)


@login_required
def edit_publication(request, subject, publication_pk):
    """
    On this page, the user edits the title, abstract, etc. for this publication.
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    publication_pk = int(publication_pk)
    # This publication
    publication = get_object_or_404(Publication, pk=publication_pk, subject=subject)
    publication_form = PublicationForm(data=data, instance=publication)
    if request.method == 'POST':
        publication_form = PublicationForm(request.POST, instance=publication)
        if publication_form.is_valid():
            with reversion.create_revision():  # Version control (django-revision)
                publication_form.save()
                reversion.set_user(request.user)
        return redirect('publication', subject=subject.slug, publication_pk=publication_pk)
    context = {
        'subject': subject,
        'publication': publication,
        'publication_form': publication_form
    }
    # Get data for the sidebar.
    status = get_status(user, subject)
    context.update(status)
    return render(request, 'publications/edit_publication.html', context)


@login_required
def experiment(request, subject, publication_pk, experiment_index):
    """
    On this page, the user chooses populations, experimental designs, and tags for this intervention (i.e. this "experiment").
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    design = subject.design  # The root design for this subject (each subject can have its own classification of designs)
    intervention = subject.intervention  # The root intervention for this subject (each subject can have its own classification of interventions)
    outcome = subject.outcome  # The root outcome for this subject (each subject can have its own classification of outcomes)
    attribute = subject.attribute  # The root attribute for this subject (each subject can have its own classification of attributes)
    attributes = Attribute.objects.get(pk=attribute.pk).get_children()
    attributes_count = attributes.count()
    # This publication
    publication = get_object_or_404(Publication, pk=publication_pk, subject=subject)
    # Formsets
    ExperimentFormSet = modelformset_factory(Experiment, form=ExperimentForm, extra=0, can_delete=False)
    ExperimentDateFormSet = modelformset_factory(ExperimentDate, form=ExperimentDateForm, extra=2, max_num=2, can_delete=True)
    ExperimentDesignFormSet = modelformset_factory(ExperimentDesign, form=ExperimentDesignForm, extra=5, max_num=5, can_delete=True)
    ExperimentPopulationFormSet = modelformset_factory(ExperimentPopulation, form=ExperimentPopulationForm, extra=4, can_delete=True)
    CoordinatesFormSet = modelformset_factory(Coordinates, form=CoordinatesForm, extra=1, can_delete=True)
    EAVFormSet = modelformset_factory(EAV, form=EAVExperimentForm, extra=attributes_count, max_num=attributes_count, can_delete=True)
    XCountryFormSet = modelformset_factory(XCountry, form=XCountryForm, extra=1, can_delete=True)
    # This experiment
    experiments = Experiment.objects.filter(publication=publication).order_by('pk')
    experiment = experiments[experiment_index]
    # Form for this experiment
    experiment_form = ExperimentForm(data=data, instance=experiment, prefix="experiment_form")
    # Show interventions for only this subject (level 0 in the classification of interventions is for different subjects, and here we show interventions for only this subject)
    experiment_form.fields['intervention'] = TreeNodeChoiceField(queryset=Intervention.objects.filter(pk=intervention.pk).get_descendants(include_self=True), level_indicator = "---")
    # Formsets for this experiment
    experiment_date_formset = ExperimentDateFormSet(data=data, queryset=ExperimentDate.objects.filter(experiment=experiment), prefix="experiment_date_formset")
    coordinates_formset = CoordinatesFormSet(data=data, queryset=Coordinates.objects.filter(experiment=experiment), prefix="coordinates_formset")
    x_country_formset = XCountryFormSet(data=data, queryset=XCountry.objects.filter(experiment=experiment), prefix="x_country_formset")
    # experiment_design_formset
    experiment_design_formset = ExperimentDesignFormSet(data=data, queryset=ExperimentDesign.objects.filter(experiment=experiment), prefix="experiment_design_formset")
    designs = TreeNodeChoiceField(required=False, queryset=Design.objects.filter(pk=design.pk).get_descendants(include_self=True).filter(level__gte=1), level_indicator = "---")
    for form in experiment_design_formset:
        form.fields['design'] = designs
    # experiment_population_formset
    experiment_population_formset = ExperimentPopulationFormSet(data=data, queryset=ExperimentPopulation.objects.filter(experiment=experiment), prefix="experiment_population_formset")
    populations = TreeNodeChoiceField(required=False, queryset=Outcome.objects.filter(pk=outcome.pk).get_descendants(include_self=True).filter(level=1), level_indicator = "---")
    for form in experiment_population_formset:
        form.fields['population'] = populations
    # EAV_formset
    EAV_formset = EAVFormSet(data=data, queryset=EAV.objects.filter(experiment=experiment), prefix="EAV_formset")
    for form in EAV_formset:
        # There should only be one instance per attribute, so we need to
        # check which attributes have instances and create extra formset forms
        # only for attributes without instances.
        if form.instance.pk is not None:
            attribute = form.instance.attribute
            attributes = attributes.exclude(attribute=attribute)
            form.unit = attribute.unit
        else:
            attribute = attributes[0]
            attributes = attributes.exclude(attribute=attribute)
            form.initial['attribute'] = attribute
            form.initial['experiment'] = experiment  # For unique_together validation
            form.initial['user'] = user  # For unique_together validation
            form.unit = attribute.unit
        if attribute.is_leaf_node():  # If factor options have not been defined, or if the data type is a number, not a factor
            form.fields['value_as_factor'].disabled = True
        else:  # If factor options have been defined (which is not possible if the data type is a number)
            form.fields['value_as_number'].disabled = True
            form.fields['value_as_factor'] = TreeNodeChoiceField(queryset=attribute.get_children(), level_indicator="")
    if request.method == 'POST':
        with transaction.atomic():
            form = experiment_form
            if form.is_valid():
                form.save()
            formset = EAV_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.experiment = experiment
                        instance.user = user
                        instance.publication_index = publication
                        instance.experiment_index = experiment
                        instance.save()
            formset = experiment_population_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.experiment = experiment
                        instance.save()
            formset = x_country_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.experiment = experiment
                        instance.experiment_index = experiment
                        instance.publication_index = publication
                        instance.user = user
                        instance.save()
            formset = experiment_date_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.experiment = experiment
                        instance.save()
            formset = experiment_design_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.experiment = experiment
                        instance.save()
            formset = coordinates_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.experiment = experiment
                        instance.publication_index = publication
                        instance.experiment_index = experiment
                        instance.user = user
                        instance.save()
            return redirect('experiment', subject=subject.slug, publication_pk=publication_pk, experiment_index=experiment_index)
    context = {
        'subject': subject,
        'publication': publication,
        'experiment': experiment,
        'experiment_index': experiment_index,
        'experiment_form': experiment_form,
        'experiment_date_formset': experiment_date_formset,
        'experiment_design_formset': experiment_design_formset,
        'experiment_population_formset': experiment_population_formset,
        'coordinates_formset': coordinates_formset,
        'EAV_formset': EAV_formset,
        'x_country_formset': x_country_formset
    }
    return render(request, 'publications/experiment.html', context)


@login_required
def population(request, subject, publication_pk, experiment_index, population_index):
    """
    On this page, the user chooses outcomes for this population.
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    attribute = subject.attribute  # The root attribute for this subject (each subject can have its own classification of attributes)
    attributes = Attribute.objects.get(pk=attribute.pk).get_children()
    attributes_count = attributes.count()
    # This publication
    publication = get_object_or_404(Publication, pk=publication_pk, subject=subject)
    # This experiment
    experiments = Experiment.objects.filter(publication=publication).order_by('pk')
    experiment = experiments[experiment_index]
    # This population
    experiment_populations = ExperimentPopulation.objects.filter(experiment=experiment).order_by('pk')
    experiment_population = experiment_populations[population_index]
    # Formsets
    ExperimentPopulationOutcomeFormSet = modelformset_factory(ExperimentPopulationOutcome, form=ExperimentPopulationOutcomeForm, extra=4, can_delete=True)
    experiment_population_outcome_formset = ExperimentPopulationOutcomeFormSet(data=data, queryset=ExperimentPopulationOutcome.objects.filter(experiment_population=experiment_population), prefix="experiment_population_outcome_formset")
    outcomes = TreeNodeChoiceField(required=False, queryset=Outcome.objects.get(pk=experiment_population.population.pk).get_descendants(include_self=True), level_indicator = "---")
    for form in experiment_population_outcome_formset:
        form.fields['outcome'] = outcomes
    EAVFormSet = modelformset_factory(EAV, form=EAVPopulationForm, extra=attributes_count, max_num=attributes_count, can_delete=True)
    EAV_formset = EAVFormSet(data=data, queryset=EAV.objects.filter(population=experiment_population), prefix="EAV_formset")
    for form in EAV_formset:
        # There should only be one instance per attribute, so we need to
        # check which attributes have instances and create extra formset forms
        # only for attributes without instances.
        if form.instance.pk is not None:
            attribute = form.instance.attribute
            attributes = attributes.exclude(attribute=attribute)
            form.unit = attribute.unit
        else:
            attribute = attributes[0]
            attributes = attributes.exclude(attribute=attribute)
            form.initial['attribute'] = attribute
            form.initial['population'] = experiment_population  # For unique_together validation
            form.initial['user'] = user  # For unique_together validation
            form.unit = attribute.unit
        if attribute.is_leaf_node():  # If factor options have not been defined, or if the data type is a number, not a factor
            form.fields['value_as_factor'].disabled = True
        else:  # If factor options have been defined (which is not possible if the data type is a number)
            form.fields['value_as_number'].disabled = True
            form.fields['value_as_factor'] = TreeNodeChoiceField(queryset=attribute.get_children(), level_indicator="")
    if request.method == 'POST':
        with transaction.atomic():
            formset = EAV_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.population = experiment_population
                        instance.user = user
                        instance.publication_index = publication
                        instance.experiment_index = experiment
                        instance.population_index = experiment_population
                        instance.save()
            formset = experiment_population_outcome_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.experiment_population = experiment_population
                        instance.save()
            return redirect('population', subject=subject.slug, publication_pk=publication_pk, experiment_index=experiment_index, population_index=population_index)
    context = {
        'subject': subject,
        'publication': publication,
        'experiment': experiment,
        'experiment_population': experiment_population,
        'experiment_index': experiment_index,
        'population_index': population_index,
        'experiment_population_outcome_formset': experiment_population_outcome_formset,
        'EAV_formset': EAV_formset
    }
    return render(request, 'publications/population.html', context)


@login_required
def outcome(request, subject, publication_pk, experiment_index, population_index, outcome_index):
    """
    On this page, the user enters effect sizes and related data for this outcome.
    """
    user = request.user
    data = request.POST or None
    subject = Subject.objects.get(slug=subject)
    attribute = subject.attribute  # The root attribute for this subject (each subject can have its own classification of attributes)
    attributes = Attribute.objects.get(pk=attribute.pk).get_children()
    attributes_count = attributes.count()
    user_subject = get_object_or_404(UserSubject, user=user, subject=subject)  # Check if this user has permission to work on this subject.
    # This publication
    publication = get_object_or_404(Publication, pk=publication_pk, subject=subject)
    # This experiment
    experiments = Experiment.objects.filter(publication=publication).order_by('pk')
    experiment = experiments[experiment_index]
    # This population
    experiment_populations = ExperimentPopulation.objects.filter(experiment=experiment).order_by('pk')
    experiment_population = experiment_populations[population_index]
    # This outcome
    experiment_population_outcomes = ExperimentPopulationOutcome.objects.filter(experiment_population=experiment_population).order_by('pk')
    experiment_population_outcome = experiment_population_outcomes[outcome_index]
    # Formsets
    DataFormSet = modelformset_factory(Data, form=DataForm, extra=1, can_delete=True)
    data_formset = DataFormSet(data=data, queryset=Data.objects.filter(experiment_population_outcome=experiment_population_outcome.pk), prefix="data_formset")
    EAVFormSet = modelformset_factory(EAV, form=EAVOutcomeForm, extra=attributes_count, max_num=attributes_count, can_delete=True)
    EAV_formset = EAVFormSet(data=data, queryset=EAV.objects.filter(outcome=experiment_population_outcome), prefix="EAV_formset")
    for form in EAV_formset:
        # There should only be one instance per attribute, so we need to
        # check which attributes have instances and create extra formset forms
        # only for attributes without instances.
        if form.instance.pk is not None:
            attribute = form.instance.attribute
            attributes = attributes.exclude(attribute=attribute)
            form.unit = attribute.unit
        else:
            attribute = attributes[0]
            attributes = attributes.exclude(attribute=attribute)
            form.initial['attribute'] = attribute
            form.initial['outcome'] = experiment_population_outcome  # For unique_together validation
            form.initial['user'] = user  # For unique_together validation
            form.unit = attribute.unit
        if attribute.is_leaf_node():  # If factor options have not been defined, or if the data type is a number, not a factor
            form.fields['value_as_factor'].disabled = True
        else:  # If factor options have been defined (which is not possible if the data type is a number)
            form.fields['value_as_number'].disabled = True
            form.fields['value_as_factor'] = TreeNodeChoiceField(queryset=attribute.get_children(), level_indicator="")
    if request.method == 'POST':
        with transaction.atomic():
            formset = EAV_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.outcome = experiment_population_outcome
                        instance.user = user
                        instance.publication_index = publication
                        instance.experiment_index = experiment
                        instance.population_index = experiment_population
                        instance.outcome_index = experiment_population_outcome
                        instance.save()
            formset = data_formset
            if formset.is_valid():
                instances = formset.save(commit=False)
                if 'delete' in request.POST:
                    for obj in formset.deleted_objects:
                        obj.delete()
                else:
                    for instance in instances:
                        instance.subject = subject
                        instance.publication = publication
                        instance.experiment = experiment
                        instance.experiment_population = experiment_population
                        instance.experiment_population_outcome = experiment_population_outcome
                        instance.save()
            return redirect('outcome', subject=subject.slug, publication_pk=publication_pk, experiment_index=experiment_index, population_index=population_index, outcome_index=outcome_index)
    context = {
        'subject': subject,
        'publication': publication,
        'experiment': experiment,
        'experiment_population': experiment_population,
        'experiment_population_outcome': experiment_population_outcome,
        'experiment_index': experiment_index,
        'population_index': population_index,
        'outcome_index': outcome_index,
        'data_formset': data_formset,
        'EAV_formset': EAV_formset
    }
    return render(request, 'publications/outcome.html', context)


def browse_by_intervention(request, subject, state):
    user = request.user
    subject = Subject.objects.get(slug=subject)
    path_to_shiny = ''
    if (state == 'publications'):
        intervention = subject.intervention    # The root intervention for this subject (each subject can have its own classification of interventions)
        interventions = Intervention.objects.filter(pk=intervention.pk).get_descendants(include_self=True)
    if (state == 'data'):
        path_to_shiny = get_path_to_shiny(request)
        data = Data.objects.filter(subject=subject)
        interventions = Intervention.objects.filter(experiment__data__in=data).get_ancestors(include_self=True)
    context = {
        'subject': subject,  # Browse within this subject
        'interventions': interventions,
        'state': state,
        'path_to_shiny': path_to_shiny
    }
    if user.is_authenticated:
        if Publication.objects.filter(subject=subject).exists():
            status = get_status(user, subject)
            context.update(status)
    return render(request, 'publications/browse_by_intervention.html', context)


def browse_by_outcome(request, subject, state):
    user = request.user
    subject = Subject.objects.get(slug=subject)
    path_to_shiny = ''
    if (state == 'publications'):
        outcome = subject.outcome  # The root outcome for this subject (each subject can have its own classification of outcomes)
        outcomes = Outcome.objects.filter(pk=outcome.pk).get_descendants(include_self=True)
    if (state == 'data'):
        path_to_shiny = get_path_to_shiny(request)
        data = Data.objects.filter(subject=subject)
        outcomes = Outcome.objects.filter(experimentpopulationoutcome__data__in=data).get_ancestors(include_self=True)
    context = {
        'subject': subject,  # Browse within this subject
        'outcomes': outcomes,
        'state': state,
        'path_to_shiny': path_to_shiny
    }
    if user.is_authenticated:
        if Publication.objects.filter(subject=subject).exists():
            status = get_status(user, subject)
            context.update(status)
    return render(request, 'publications/browse_by_outcome.html', context)


def this_intervention(request, subject, state, intervention_pk, outcome_pk='default'):
    user = request.user
    subject = Subject.objects.get(slug=subject)
    path = ''
    path_to_shiny = ''
    this_intervention = Intervention.objects.get(pk=intervention_pk)
    interventions = Intervention.objects.filter(pk=intervention_pk).get_descendants(include_self=True)
    if outcome_pk != 'default':
        this_outcome = Outcome.objects.get(pk=outcome_pk)
        outcomes = Outcome.objects.filter(pk=outcome_pk).get_descendants(include_self=True)
    if state == 'publications':
        # Publications for this intervention (and its descendants)
        publications = Publication.objects.filter(subject=subject)
        publications = publications.distinct().filter(experiment__intervention__in=interventions)
        # Filter these publications by outcome
        if outcome_pk != 'default':
            publications = publications.distinct().filter(
                    Q(experiment__experimentpopulation__experimentpopulationoutcome__outcome__in=outcomes) |
                    Q(publicationpopulation__publicationpopulationoutcome__outcome__in=outcomes)
                )
            # Pass this path to the template for evidence-atlas.js to generate dynamic links by intervention and outcome.
            path = reverse('publications_x', args=(), kwargs={'subject': subject.slug, 'intervention_pk': this_intervention.pk, 'outcome_pk': this_outcome.pk})
        else:
            this_outcome = None
            # Pass this path to the template for evidence-atlas.js to generate dynamic links by intervention (not outcome).
            path = reverse('publications_x', args=(), kwargs={'subject': subject.slug, 'intervention_pk': this_intervention.pk})

        # Outcomes for these publications
        # By publication (outcomes can be entered by publication or by experiment)
        publication_population_outcomes = PublicationPopulationOutcome.objects.filter(
            publication_population__publication__in=publications)
        # By experiment (outcomes can be entered by publication or by experiment)
        experiment_population_outcomes = ExperimentPopulationOutcome.objects.filter(
            experiment_population__experiment__publication__in=publications)
        # All outcomes for these publications (outcomes by publication OR outcomes by experiment)
        outcomes = Outcome.objects.distinct().filter(
                Q(experimentpopulationoutcome__in=experiment_population_outcomes) |
                Q(publicationpopulationoutcome__in=publication_population_outcomes)
            ).get_ancestors(include_self=True)

        # Countries for these publications
        countries = XCountry.objects.filter(publication_index__in=publications)

        # The number of publications by country
        q = countries.values_list('country__iso_alpha_3', 'publication_index').distinct()
        countries = list(chain(q))  # A list of tuples in the form [(country, publication)]. Chain is imported from itertools.
        countries = set(countries)  # Delete duplicate records, where a publication has the same country in both publication_country and experiment_country: set = unique tuples (and the list is now a dict)
        count_by_country = Counter(item[0] for item in countries)  # item[0] is country in (country, publication) and this counts the number of tuples for each country. Counter is imported from collections.
        count_by_country = json.dumps(count_by_country)  # Convert to JSON for use by JavaScript in the template
        count = publications.count()

    if state == 'data':
        path_to_shiny = get_path_to_shiny(request)

        # Data for this intervention (and its descendants)
        data = Data.objects.filter(subject=subject)
        data = data.filter(experiment__intervention__in=interventions)
        # Filter these data by outcome
        if outcome_pk != 'default':
            data = data.filter(experiment_population_outcome__outcome__in=outcomes)
            # Pass this path to the template for evidence-atlas.js to generate dynamic links by intervention and outcome.
            path = "{path_to_shiny}?subject={subject}&intervention={intervention}&outcome={outcome}&country=".format(path_to_shiny=path_to_shiny, subject=subject.pk, intervention=this_intervention.pk, outcome=this_outcome.pk)
        else:
            this_outcome = None
            # Pass this path to the template for evidence-atlas.js to generate dynamic links by intervention (not outcome).
            path = "{path_to_shiny}?subject={subject}&intervention={intervention}&country=".format(path_to_shiny=path_to_shiny, subject=subject.pk, intervention=this_intervention.pk)

        # Outcomes for these data
        outcomes = Outcome.objects.distinct().filter(
                experimentpopulationoutcome__data__in=data
            ).get_ancestors(include_self=True)

        # Countries for these data
        experiments = Experiment.objects.filter(data__in=data)
        countries = XCountry.objects.filter(experiment_index__in=experiments)
        q = countries.values_list('country__iso_alpha_3', 'experiment_index__data').distinct()
        countries = list(chain(q))  # A list of tuples in the form [(country, publication)]. Chain is imported from itertools.
        countries = set(countries)  # Delete duplicate records, where a publication has the same country in both publication_country and experiment_country: set = unique tuples (and the list is now a dict)
        count_by_country = Counter(item[0] for item in countries)  # item[0] is country in (country, publication) and this counts the number of tuples for each country. Counter is imported from collections.
        count_by_country = json.dumps(count_by_country)  # Convert to JSON for use by JavaScript in the template
        count = data.count()

    context = {
        'subject': subject,
        'this_intervention': this_intervention,
        'this_outcome': this_outcome,
        'outcomes': outcomes,
        'count': count,
        'count_by_country': count_by_country,
        'path': path,
        'path_to_shiny': path_to_shiny,
        'state': state
    }
    if user.is_authenticated:
        if Publication.objects.filter(subject=subject).exists():
            status = get_status(user, subject)
            context.update(status)
    return render(request, 'publications/this_intervention.html', context)


def this_outcome(request, subject, state, outcome_pk, intervention_pk='default'):
    user = request.user
    subject = Subject.objects.get(slug=subject)
    path = ''
    path_to_shiny = ''
    this_outcome = Outcome.objects.get(pk=outcome_pk)
    outcomes = Outcome.objects.filter(pk=outcome_pk).get_descendants(include_self=True)
    if state == 'publications':
        # Records for these outcomes
        publication_population_outcomes = PublicationPopulationOutcome.objects.filter(outcome__in=outcomes)
        experiment_population_outcomes = ExperimentPopulationOutcome.objects.filter(outcome__in=outcomes)
        # Publications for these records
        publications = Publication.objects.distinct().filter(subject=subject)
        publications = publications.distinct().filter(
                Q(experiment__experimentpopulation__experimentpopulationoutcome__in=experiment_population_outcomes) |
                Q(publicationpopulation__publicationpopulationoutcome__in=publication_population_outcomes)
            )
        # Filter these publications by intervention
        if intervention_pk != 'default':
            this_intervention = Intervention.objects.get(pk=intervention_pk)
            interventions = Intervention.objects.filter(pk=intervention_pk).get_descendants(include_self=True)
            # Publications for these interventions
            publications = publications.distinct().filter(experiment__intervention__in=interventions)
            # Pass this path to the template for evidence-atlas.js to generate dynamic links by intervention and outcome.
            path = reverse('publications_x', args=(), kwargs={'subject': subject.slug, 'intervention_pk': this_intervention.pk, 'outcome_pk': this_outcome.pk})
        else:
            this_intervention = None
            # Pass this path to the template for evidence-atlas.js to generate dynamic links by outcome (not intervention).
            path = reverse('publications_x', args=(), kwargs={'subject': subject.slug, 'outcome_pk': this_outcome.pk})
        # Interventions for these publications
        interventions = Intervention.objects.distinct().filter(
                experiment__publication__in=publications
            ).get_ancestors(include_self=True)
        # Countries for these publications
        countries = XCountry.objects.filter(publication_index__in=publications)
        # The number of publications by country
        q = countries.values_list('country__iso_alpha_3', 'publication_index').distinct()
        countries = list(chain(q))  # A list of tuples in the form [(country, publication)]. Chain is imported from itertools.
        countries = set(countries)  # Delete duplicate records, where a publication has the same country in both publication_country and experiment_country: set = unique tuples (and the list is now a dict)
        count_by_country = Counter(item[0] for item in countries)  # item[0] is country in (country, publication) and this counts the number of tuples for each country. Counter is imported from collections.
        count_by_country = json.dumps(count_by_country)  # Convert to JSON for use by JavaScript in the template
        count = publications.count()

    if state == 'data':
        path_to_shiny = get_path_to_shiny(request)

        # Data for this outcome (and its descendants)
        data = Data.objects.filter(subject=subject)
        data = data.filter(experiment_population_outcome__outcome__in=outcomes)
        # Filter these data by intervention
        if intervention_pk != 'default':
            data = data.filter(experiment__intervention__in=interventions)
            # Pass this path to the template for evidence-atlas.js to generate dynamic links by intervention and outcome.
            path = "{path_to_shiny}?subject={subject}&intervention={intervention}&outcome={outcome}&country=".format(path_to_shiny=path_to_shiny, subject=subject.pk, intervention=this_intervention.pk, outcome=this_outcome.pk)
        else:
            this_intervention = None
            # Pass this path to the template for evidence-atlas.js to generate dynamic links by outcome (not intervention).
            path = "{path_to_shiny}?subject={subject}&outcome={outcome}&country=".format(path_to_shiny=path_to_shiny, subject=subject.pk, outcome=this_outcome.pk)
        # Interventions for these data
        interventions = Intervention.objects.distinct().filter(
                experiment__data__in=data
            ).get_ancestors(include_self=True)

        # Countries for these data
        # Countries by experiment
        experiments = Experiment.objects.filter(data__in=data)
        countries = XCountry.objects.filter(experiment_index__in=experiments)
        q = countries.values_list('country__iso_alpha_3', 'experiment_index__data').distinct()
        countries = list(chain(q))  # A list of tuples in the form [(country, publication)]. Chain is imported from itertools.
        countries = set(countries)  # Delete duplicate records, where a publication has the same country in both publication_country and experiment_country: set = unique tuples (and the list is now a dict)
        count_by_country = Counter(item[0] for item in countries)  # item[0] is country in (country, publication) and this counts the number of tuples for each country. Counter is imported from collections.
        count_by_country = json.dumps(count_by_country)  # Convert to JSON for use by JavaScript in the template
        count = data.count()

    context = {
        'subject': subject,
        'this_intervention': this_intervention,
        'this_outcome': this_outcome,
        'interventions': interventions,
        'count': count,
        'count_by_country': count_by_country,
        'path': path,
        'path_to_shiny': path_to_shiny,
        'state': state
    }
    if user.is_authenticated:
        if Publication.objects.filter(subject=subject).exists():
            status = get_status(user, subject)
            context.update(status)
    return render(request, 'publications/this_outcome.html', context)


def publications_x(request, subject, intervention_pk='default', outcome_pk='default', iso_a3='default'):
    user = request.user
    subject = Subject.objects.get(slug=subject)
    publications = Publication.objects.filter(subject=subject)

    # Publications that have been marked as "completed"
#    publications = publications.distinct().filter(assessment__is_completed=True)

    if iso_a3 != 'default':
        if iso_a3 != '-99':  # Disputed territories that are not our Countries model: Kosovo, Northern Cyprus, and Somaliland
            country = Country.objects.get(iso_alpha_3=iso_a3)
            publications = publications.distinct().filter(xcountry_publication_index__country=country)
    if outcome_pk != 'default':
        outcomes = Outcome.objects.filter(pk=outcome_pk).get_descendants(include_self=True)
        # Outcomes by experiment (outcomes can be entered by experiment or by publication)
        experiment_population_outcomes = ExperimentPopulationOutcome.objects.filter(outcome__in=outcomes)
        # Outcomes by publication (outcomes can be entered by experiment or by publication)
        publication_population_outcomes = PublicationPopulationOutcome.objects.filter(outcome__in=outcomes)
        # Publications for these outcomes
        publications = publications.distinct().filter(
                Q(experiment__experimentpopulation__experimentpopulationoutcome__in=experiment_population_outcomes) |
                Q(publicationpopulation__publicationpopulationoutcome__in=publication_population_outcomes)
            )
    if intervention_pk != 'default':
        interventions = Intervention.objects.filter(pk=intervention_pk).get_descendants(include_self=True)
        publications = publications.distinct().filter(experiment__intervention__in=interventions)
    publications = publications.order_by('title')
    if iso_a3 == '-99':  # Disputed territories that are not our Countries model: Kosovo, Northern Cyprus, and Somaliland
        publications = Publication.objects.none()
    page = request.GET.get('page', 1)
    paginator = Paginator(publications, 10)
    try:
        publications = paginator.page(page)
    except PageNotAnInteger:
        publications = paginator.page(1)
    except EmptyPage:
        publications = paginator.page(paginator.num_pages)
    context = {
        'subject': subject,
        'publications': publications
    }
    if user.is_authenticated:
        if Publication.objects.filter(subject=subject).exists():
            status = get_status(user, subject)
            context.update(status)
    return render(request, 'publications/publications.html', context)


def get_status(user, subject):
    """
    Publications should be assessed in a random order, but each user should see
    the same order from session to session. Therefore, a random assessment_order
    is created for each user (for each subject), and it is saved in the database.
    """

    # If an assessment_order has been created for this user and subject, get it from the database.
    if AssessmentStatus.objects.filter(user=user, subject=subject).exists():
        item = AssessmentStatus.objects.get(user=user, subject=subject)
        assessment_order = literal_eval(item.assessment_order)
        next_assessment = item.next_assessment
        completed_assessments = literal_eval(item.completed_assessments)

        # If new publications have been added to the database, then randomly append their pks to the end of assessment_order.
        max_assessment_pks = max(assessment_order)
        pks = Publication.objects.filter(subject=subject).values_list('pk', flat=True)
        max_pks = max(pks)

        if max_assessment_pks < max_pks:
            new_publications = list(pks)
            new_publications = list(set(new_publications) - set(assessment_order))
            shuffle(new_publications)
            assessment_order = assessment_order + new_publications
            item.assessment_order = assessment_order
            item.save()

        #TODO: If old publications have been deleted from the database (this should not happen in production), then delete their pks from assessment_order.

    # If an assessment_order has not been created for this user and subject, create it and save it in the database.
    else:
        pks = Publication.objects.filter(subject=subject).values_list('pk', flat=True)
        assessment_order = list(pks)
        shuffle(assessment_order)
        next_assessment = assessment_order[0]
        previous_full_text_assessment = -1
        completed_assessments = []
        item = AssessmentStatus(
            subject=subject,
            user=user,
            assessment_order=assessment_order,
            next_assessment=next_assessment,
            previous_full_text_assessment=previous_full_text_assessment,
            completed_assessments=completed_assessments
        )
        item.save()
    item = AssessmentStatus.objects.get(user=user, subject=subject)
    publications_count = len(assessment_order)
    publications_assessed_count = len(completed_assessments)
    if publications_count != 0:
        publications_assessed_percent = int(publications_assessed_count / publications_count * 100)
    else:
        publications_assessed_percent = 100
    # Count the publications that have been assessed as relevant based on the title/abstract
    if Publication.objects.filter(assessment__in=Assessment.objects.filter(
        subject=subject, user=user, is_relevant=True)).exists():
        relevant_publications_count = Publication.objects.filter(
            assessment__in=Assessment.objects.filter(
                subject=subject, user=user, is_relevant=True)).count()
    else:
        relevant_publications_count = 0
    # Count the publications that have been marked as completed
    if Publication.objects.filter(assessment__in=Assessment.objects.filter(
        subject=subject, user=user, is_completed=True)).exists():
        full_texts_assessed_count = Publication.objects.filter(
            assessment__in=Assessment.objects.filter(
                subject=subject, user=user, is_completed=True)).count()
    else:
        full_texts_assessed_count = 0
    if relevant_publications_count != 0:
        full_texts_assessed_percent = int(full_texts_assessed_count / relevant_publications_count * 100)
    else:
        full_texts_assessed_percent = 100
    status = {
        'user_subject': UserSubject.objects.filter(user=user, subject=subject).exists(),
        'item': item,
        'publications_count': publications_count,
        'publications_assessed_count': publications_assessed_count,
        'publications_assessed_percent': publications_assessed_percent,
        'full_texts_assessed_count': full_texts_assessed_count,
        'full_texts_assessed_percent': full_texts_assessed_percent,
        'relevant_publications_count': relevant_publications_count,
        'next_assessment': next_assessment
    }
    return(status)


# This method is needed (as are the lists of completed_assessments), because
# we need to maintain a unique random order for each user. Otherwise, we could
# use querysets for navigation, as we do for full_text_navigation.
def get_next_assessment(publication_pk, next_pk, assessment_order, completed_assessments):
    next_assessment = next_pk
    uncompleted_assessments = list(set(assessment_order) - set(completed_assessments))
    if next_assessment in uncompleted_assessments:
        return(next_assessment)
    else:
        if uncompleted_assessments:
            next_assessment = uncompleted_assessments[0]
            if next_assessment == publication_pk:  # Allow users to skip this publication.
                try:
                    next_assessment = uncompleted_assessments[uncompleted_assessments.index(next_assessment) + 1]
                except:
                    next_assessment = uncompleted_assessments[0]
        return(next_assessment)


def get_path_to_shiny(request):
    current_site = get_current_site(request)
    domain = current_site.domain
    if domain == "www.metadataset.com":
        path_to_shiny = "http://shiny.metadataset.com/meta-analysis/"
    else:
        path_to_shiny = "http://127.0.0.1:7099/"
    return(path_to_shiny)


@login_required
def full_text_navigation(request, subject, state, publication_pk='default'):
    user = request.user
    subject = Subject.objects.get(slug=subject)
    # Get the publication from which to calculate "next" and "previous" (either the previous_full_text_assessment or the publication from which the request was sent).
    if (publication_pk=='default'):
        previous_full_text_assessment = AssessmentStatus.objects.get(
            subject=subject, user=user).previous_full_text_assessment
        if (previous_full_text_assessment == -1):  # If this is a new user, the initial value will be -1.
            previous_full_text_assessment = Publication.objects.filter(
                subject=subject
            ).order_by('-title').values_list('pk', flat=True)[0]
            assessment_status = AssessmentStatus.objects.get(
                subject=subject, user=user)
            assessment_status.previous_full_text_assessment = previous_full_text_assessment
            assessment_status.save
        publication = Publication.objects.get(pk=previous_full_text_assessment)
    else:
        publication = Publication.objects.get(pk=int(publication_pk))
    # Get all the publications.
    publications = Publication.objects.filter(subject=subject)
    # Exclude this publication.
    publications = publications.exclude(pk=publication.pk)
    if (state == 'next-incomplete' or state == 'previous-incomplete'):
        # If there are publications for this subject that this user has assessed as relevant and has not yet marked as completed
        if publications.filter(assessment__in=Assessment.objects.filter(
            subject=subject, user=user, is_relevant=True, is_completed=False
        )).exists():
            publications = publications.filter(assessment__in=Assessment.objects.filter(
                subject=subject, user=user, is_relevant=True, is_completed=False
            ))
        # Else if there are publications for this subject that this user has assessed as relevant but all of them have been marked as completed
        elif publications.filter(assessment__in=Assessment.objects.filter(
            subject=subject, user=user, is_relevant=True
        )).exists():
            publications = publications.filter(assessment__in=Assessment.objects.filter(
                subject=subject, user=user, is_relevant=True
            ))
        if (state == 'next-incomplete'):
            try:
                publication_pk = publications.filter(
                    title__gte=publication.title  # Titles later in the alphabet
                ).order_by('title').values_list('pk', flat=True)[0]
            except:
                publication_pk = publications.order_by('title').values_list('pk', flat=True)[0]
        elif (state == 'previous-incomplete'):
            try:
                publication_pk = publications.filter(
                    title__lte=publication.title  # Titles earlier in the alphabet
                ).order_by('-title').values_list('pk', flat=True)[0]
            except:
                publication_pk = publications.order_by('-title').values_list('pk', flat=True)[0]
    elif (state == 'next' or state == 'previous'):
        if publications.filter(assessment__in=Assessment.objects.filter(
            subject=subject, user=user, is_relevant=True
        )).exists():
            publications = publications.filter(assessment__in=Assessment.objects.filter(
                subject=subject, user=user, is_relevant=True
            ))
            if (state == 'next'):
                try:
                    publication_pk = publications.filter(
                        title__gte=publication.title  # Titles later in the alphabet
                    ).order_by('title').values_list('pk', flat=True)[0]
                except:
                    publication_pk = publications.order_by('title').values_list('pk', flat=True)[0]
            elif (state == 'previous'):
                try:
                    publication_pk = publications.filter(
                        title__lte=publication.title  # Titles earlier in the alphabet
                    ).order_by('-title').values_list('pk', flat=True)[0]
                except:
                    publication_pk = publications.order_by('-title').values_list('pk', flat=True)[0]
    # If there are no full texts for this subject that the user has assessed as relevant
    if not publications.filter(assessment__in=Assessment.objects.filter(
        subject=subject, user=user, is_relevant=True
    )).exists():
        publication_pk = Publication.objects.filter(
            subject=subject
        ).order_by('title').values_list('pk', flat=True)[0]
    # Update the current full_text_assessment
    assessment_status = AssessmentStatus.objects.get(subject=subject, user=user)
    assessment_status.previous_full_text_assessment = publication_pk
    assessment_status.save()
    return redirect('publication', subject=subject.slug, publication_pk=publication_pk)
